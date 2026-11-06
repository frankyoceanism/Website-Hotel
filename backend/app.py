import os
import re
import secrets
import sys
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import wraps

import mysql.connector
from flask import (
    Flask, abort, flash, g, jsonify, redirect,
    render_template, request, session
)
from werkzeug.security import check_password_hash, generate_password_hash


# =========================
# KONFIGURASI
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"

app = Flask(__name__)


def muat_secret_key():
    """SECRET_KEY dari environment; kalau tidak ada, disimpan di file
    .secret_key supaya login tidak hilang saat server restart."""
    dari_env = os.environ.get("SECRET_KEY")
    if dari_env:
        return dari_env

    path = os.path.join(BASE_DIR, ".secret_key")
    try:
        with open(path, encoding="utf-8") as f:
            kunci = f.read().strip()
        if kunci:
            return kunci
    except OSError:
        pass

    kunci = secrets.token_hex(32)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(kunci)
        os.chmod(path, 0o600)
    except OSError:
        pass
    return kunci


app.secret_key = muat_secret_key()
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)

# Sama dengan konfigurasi lama: localhost / root / (kosong) / hotel
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "hotel"),
}
NAMA_DB = DB_CONFIG["database"]

if not re.match(r"^[A-Za-z0-9_]+$", NAMA_DB):
    sys.exit("DB_NAME hanya boleh huruf, angka, dan garis bawah.")

STATUS_MENUNGGU = "Menunggu"
STATUS_LUNAS = "lunas"
STATUS_BATAL = "batal"
KAMAR_TERSEDIA = "Tersedia"
KAMAR_TIDAK = "Tidak Tersedia"

MAX_MALAM = 365
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,50}$")
SUDAH_HASH = ("pbkdf2:", "scrypt:")

ADMIN_DEFAULT_USER = "admin"
ADMIN_DEFAULT_PASS = "admin123"

# Nilai role untuk user biasa (disesuaikan dengan tabel users yang ada)
ROLE_CUSTOMER = "customer"

# Akhiran query untuk mengunci baris (dikosongkan saat tes)
LOCK = " FOR UPDATE"

GAGAL_LOGIN = {}
MAX_GAGAL = 10
JENDELA_DETIK = 300


# =========================
# DATABASE (MySQL)
# =========================

def koneksi(dengan_db=True):
    cfg = dict(DB_CONFIG)
    if not dengan_db:
        cfg.pop("database")
    return mysql.connector.connect(autocommit=True, **cfg)


def get_db():
    if "db" not in g:
        g.db = koneksi()
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        try:
            if db.is_connected():
                db.close()
        except mysql.connector.Error:
            pass


def fetch_all(sql, params=()):
    cur = get_db().cursor(dictionary=True, buffered=True)
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()


def fetch_one(sql, params=()):
    cur = get_db().cursor(dictionary=True, buffered=True)
    try:
        cur.execute(sql, params)
        return cur.fetchone()
    finally:
        cur.close()


def execute_write(sql, params=()):
    cur = get_db().cursor(buffered=True)
    try:
        cur.execute(sql, params)
        return cur.rowcount
    finally:
        cur.close()


@contextmanager
def transaksi():
    """Satu transaksi: commit kalau sukses, rollback kalau ada error."""
    db = get_db()
    cur = db.cursor(dictionary=True, buffered=True)
    try:
        db.start_transaction()
        yield cur
        db.commit()
    except Exception:
        try:
            db.rollback()
        except mysql.connector.Error:
            pass
        raise
    finally:
        cur.close()


# =========================
# INISIALISASI DATABASE
# (tidak menghapus / mengubah data; hanya melengkapi yang kurang)
# =========================

SKEMA = [
    """CREATE TABLE IF NOT EXISTS users (
        id_user  INT AUTO_INCREMENT PRIMARY KEY,
        nama     VARCHAR(100) NOT NULL,
        username VARCHAR(50)  NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        role     VARCHAR(20)  NOT NULL DEFAULT 'customer'
    )""",
    """CREATE TABLE IF NOT EXISTS rooms (
        id_room         INT AUTO_INCREMENT PRIMARY KEY,
        nomor_kamar     VARCHAR(10) NOT NULL UNIQUE,
        tipe_kamar      VARCHAR(50) NOT NULL,
        harga_per_malam DECIMAL(12,2) NOT NULL,
        status          VARCHAR(20) NOT NULL DEFAULT 'Tersedia'
    )""",
    """CREATE TABLE IF NOT EXISTS addons (
        id_addon   INT AUTO_INCREMENT PRIMARY KEY,
        nama_addon VARCHAR(100) NOT NULL,
        harga      DECIMAL(12,2) NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS bookings (
        id_booking       INT AUTO_INCREMENT PRIMARY KEY,
        id_user          INT NOT NULL,
        id_room          INT NOT NULL,
        tanggal_checkin  DATE NOT NULL,
        tanggal_checkout DATE NOT NULL,
        total_harga      DECIMAL(14,2) NOT NULL,
        status           VARCHAR(20) NOT NULL DEFAULT 'Menunggu',
        INDEX idx_room_tanggal (id_room, tanggal_checkin, tanggal_checkout)
    )""",
    """CREATE TABLE IF NOT EXISTS booking_addons (
        id_booking INT NOT NULL,
        id_addon   INT NOT NULL,
        PRIMARY KEY (id_booking, id_addon)
    )""",
]

KOLOM_WAJIB = {
    "users": ["id_user", "nama", "username", "password", "role"],
    "rooms": ["id_room", "nomor_kamar", "tipe_kamar",
            "harga_per_malam", "status"],
    "addons": ["id_addon", "nama_addon", "harga"],
    "bookings": ["id_booking", "id_user", "id_room", "tanggal_checkin",
                "tanggal_checkout", "total_harga", "status"],
    "booking_addons": ["id_booking", "id_addon"],
}


def _s(v):
    return v.decode("utf-8", "replace") if isinstance(v, (bytes, bytearray)) else v


def _nilai_enum(tipe):
    return [v.replace("''", "'")
            for v in re.findall(r"'((?:[^']|'')*)'", tipe)]


def info_kolom(cur, tabel, kolom):
    """(tipe, panjang) kolom, atau None kalau kolom tidak ada."""
    cur.execute(
        "SELECT COLUMN_TYPE, CHARACTER_MAXIMUM_LENGTH "
        "FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        (NAMA_DB, tabel, kolom)
    )
    baris = cur.fetchall()
    if not baris:
        return None
    tipe, panjang = baris[0][0], baris[0][1]
    return str(_s(tipe)), (int(panjang) if panjang is not None else None)


def lebarkan_kolom_teks(cur, tabel, kolom, wajib, default):
    """Kalau kolom ENUM tidak memuat semua nilai yang dibutuhkan, atau
    VARCHAR-nya terlalu pendek, ubah jadi VARCHAR(20). Data tidak hilang."""
    info = info_kolom(cur, tabel, kolom)
    if info is None:
        return
    tipe, panjang = info

    if tipe.lower().startswith("enum"):
        ada = {v.lower() for v in _nilai_enum(tipe)}
        perlu = not {w.lower() for w in wajib} <= ada
    else:
        perlu = panjang is not None and panjang < 20

    if perlu:
        cur.execute(
            f"ALTER TABLE `{tabel}` MODIFY `{kolom}` "
            f"VARCHAR(20) NOT NULL DEFAULT '{default}'"
        )
        print(f"[INFO] Kolom {tabel}.{kolom} dilebarkan ke VARCHAR(20) "
            f"(data tetap utuh).")


def init_db():
    global ROLE_CUSTOMER

    try:
        db = koneksi(dengan_db=False)
        cur = db.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{NAMA_DB}` "
                    "CHARACTER SET utf8mb4")
        db.close()

        db = koneksi()
        cur = db.cursor()

        for ddl in SKEMA:
            cur.execute(ddl)

        # Hash password lebih panjang dari 50-100 karakter
        info = info_kolom(cur, "users", "password")
        if info and info[1] is not None and info[1] < 255:
            cur.execute("ALTER TABLE users MODIFY password "
                        "VARCHAR(255) NOT NULL")
            print("[INFO] Kolom users.password dilebarkan ke VARCHAR(255).")

        lebarkan_kolom_teks(cur, "bookings", "status",
                            [STATUS_MENUNGGU, STATUS_LUNAS, STATUS_BATAL],
                            STATUS_MENUNGGU)
        lebarkan_kolom_teks(cur, "rooms", "status",
                            [KAMAR_TERSEDIA, KAMAR_TIDAK], KAMAR_TERSEDIA)

        # Nilai role untuk user biasa mengikuti isi tabel yang ada
        info = info_kolom(cur, "users", "role")
        if info and info[0].lower().startswith("enum"):
            nilai = _nilai_enum(info[0])
            bukan_admin = [v for v in nilai if v.lower() != "admin"]
            if "customer" in nilai:
                ROLE_CUSTOMER = "customer"
            elif bukan_admin:
                ROLE_CUSTOMER = bukan_admin[0]

        # Data awal hanya kalau tabelnya kosong
        cur.execute("SELECT COUNT(*) FROM rooms")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO rooms (nomor_kamar, tipe_kamar, "
                "harga_per_malam, status) VALUES (%s, %s, %s, %s)",
                [("101", "Standard", 350000, KAMAR_TERSEDIA),
                ("102", "Standard", 350000, KAMAR_TERSEDIA),
                ("201", "Deluxe", 550000, KAMAR_TERSEDIA),
                ("301", "Suite", 950000, KAMAR_TERSEDIA)])

        cur.execute("SELECT COUNT(*) FROM addons")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO addons (nama_addon, harga) VALUES (%s, %s)",
                [("Sarapan", 75000), ("Antar-jemput bandara", 150000),
                ("Late check-out", 100000)])

        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO users (nama, username, password, role) "
                "VALUES (%s, %s, %s, 'admin')",
                ("Administrator", ADMIN_DEFAULT_USER,
                generate_password_hash(ADMIN_DEFAULT_PASS)))
            print(f"\n>>> Akun admin dibuat: username "
                f"'{ADMIN_DEFAULT_USER}', password "
                f"'{ADMIN_DEFAULT_PASS}' (segera ganti) <<<\n")

        # Laporan: kolom yang dibutuhkan aplikasi tapi tidak ada
        print("=== Cek database ===")
        bermasalah = False
        for tabel, kolom in KOLOM_WAJIB.items():
            cur.execute(f"SHOW COLUMNS FROM `{tabel}`")
            ada = {str(_s(r[0])) for r in cur.fetchall()}
            kurang = [k for k in kolom if k not in ada]
            if kurang:
                bermasalah = True
                print(f"[MASALAH] Tabel {tabel}: kolom kurang -> "
                    f"{', '.join(kurang)}")
        if not bermasalah:
            print(f"[OK] Terhubung ke database '{NAMA_DB}', semua tabel "
                f"dan kolom lengkap.")
        print("====================")
        db.close()

    except mysql.connector.Error as e:
        print("\n[MASALAH] Tidak bisa menyiapkan database MySQL:", e)
        print("Cek: MySQL sudah menyala? DB_HOST / DB_USER / DB_PASSWORD "
            "sudah benar?\n")


# =========================
# PEMERIKSA TEMPLATE
# =========================

TEMPLATE_WAJIB = ["base.html", "error.html", "login.html", "register.html",
                "rooms.html", "booking.html", "bookings.html",
                "payment.html", "admin.html"]


def periksa_template():
    """Deteksi file template yang hilang, salah isi, atau versi lama."""
    from jinja2 import TemplateSyntaxError

    folder = os.path.join(app.root_path, app.template_folder or "templates")
    masalah = []

    for nama in TEMPLATE_WAJIB:
        path = os.path.join(folder, nama)
        if not os.path.exists(path):
            masalah.append(f"{nama}: file tidak ditemukan di folder templates")
            continue

        try:
            with open(path, encoding="utf-8") as f:
                sumber = f.read()
        except (OSError, UnicodeDecodeError) as e:
            masalah.append(f"{nama}: tidak bisa dibaca ({e})")
            continue

        try:
            app.jinja_env.parse(sumber)
        except TemplateSyntaxError as e:
            masalah.append(f"{nama}: salah sintaks baris {e.lineno} ({e.message})")
            continue

        meluas = re.findall(r"{%-?\s*extends\s+[\"']([^\"']+)[\"']", sumber)

        if nama == "base.html":
            if meluas:
                masalah.append("base.html: TIDAK BOLEH memakai {% extends %} "
                            "(isinya salah / tertimpa file lain). "
                            "Ganti dengan base.html dari hotel.zip")
        elif meluas != ["base.html"]:
            masalah.append(f"{nama}: harus diawali {{% extends \"base.html\" %}}"
                        " (ini kemungkinan versi lama)")

        if "<form" in sumber and 'name="csrf_token"' not in sumber:
            masalah.append(f"{nama}: form tanpa csrf_token (versi lama), "
                        "login/daftar/bayar akan ditolak")

    print("=== Cek template ===")
    if masalah:
        for m in masalah:
            print("[MASALAH]", m)
        print("Solusi: ekstrak ulang hotel.zip, salin SEMUA isi folder "
            "templates, lalu Save All.")
    else:
        print("[OK] Semua template lengkap dan versi terbaru.")
    print("====================")


# =========================
# HELPER
# =========================

@app.template_filter("rupiah")
def rupiah(nilai):
    try:
        return "Rp" + f"{int(nilai):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "Rp0"


def to_jsonable(rows):
    hasil = []
    for row in rows:
        item = {}
        for k, v in row.items():
            if isinstance(v, Decimal):
                v = float(v)
            elif isinstance(v, (datetime, date, timedelta)):
                v = str(v)
            elif isinstance(v, (bytes, bytearray)):
                v = v.decode("utf-8", errors="replace")
            item[k] = v
        hasil.append(item)
    return hasil


def halaman_error(pesan, kode=400, detail=None, petunjuk=None):
    try:
        return render_template(
            "error.html", pesan=pesan, kode=kode, petunjuk=petunjuk,
            detail=detail if app.debug else None
        ), kode
    except Exception:
        # Kalau error.html sendiri rusak, jangan sampai error berantai
        app.logger.exception("error.html gagal ditampilkan")
        return f"Error {kode}: {pesan}", kode


def petunjuk_db(e):
    """Saran perbaikan berdasarkan kode error MySQL."""
    kode = getattr(e, "errno", None)

    if kode in (2002, 2003, 2006, 2013, 2055):
        return ("Tidak bisa terhubung ke MySQL. Pastikan MySQL sudah menyala "
                "(di XAMPP: klik Start pada baris MySQL), lalu periksa "
                "DB_HOST dan DB_PORT.")
    if kode in (1044, 1045):
        return ("Username atau password MySQL ditolak. Set DB_USER dan "
                "DB_PASSWORD sesuai akun MySQL kamu.")
    if kode == 1049:
        return ("Database tidak ditemukan. Periksa nama database (DB_NAME), "
                "atau jalankan ulang python app.py supaya dibuat otomatis.")
    if kode == 1146:
        return ("Tabel belum ada. Jalankan ulang python app.py supaya tabel "
                "dibuat otomatis.")
    if kode == 1054:
        return ("Ada kolom yang dibutuhkan aplikasi tapi tidak ada di "
                "tabelmu. Lihat bagian '=== Cek database ===' di terminal.")
    return None


def parse_harga(teks):
    try:
        nilai = int(str(teks).strip())
    except ValueError:
        return None
    return nilai if 0 < nilai <= 1_000_000_000 else None


def password_cocok(tersimpan, diketik):
    """Hash baru, atau password lama (plain text) dari versi sebelumnya."""
    tersimpan = tersimpan or ""

    if not tersimpan or not diketik:
        return False

    if tersimpan.startswith(SUDAH_HASH):
        try:
            return check_password_hash(tersimpan, diketik)
        except ValueError:
            return False

    return secrets.compare_digest(
        tersimpan.encode("utf-8"), diketik.encode("utf-8")
    )


def terlalu_banyak_gagal(ip):
    sekarang = time.time()
    daftar = [t for t in GAGAL_LOGIN.get(ip, []) if sekarang - t < JENDELA_DETIK]
    GAGAL_LOGIN[ip] = daftar
    return len(daftar) >= MAX_GAGAL


def catat_gagal(ip):
    GAGAL_LOGIN.setdefault(ip, []).append(time.time())


# =========================
# KEAMANAN: CSRF + AKSES
# =========================

@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.get("csrf_token", "")
        kiriman = request.form.get("csrf_token", "")
        if not token:
            abort(400, description=(
                "CSRF: browser tidak mengirim cookie sesi (cookie diblokir, "
                "sesi habis, atau alamat yang dibuka berbeda)."))
        if not secrets.compare_digest(token, kiriman):
            abort(400, description="CSRF: token form tidak cocok dengan sesi.")


@app.context_processor
def inject_csrf():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return {"csrf_token": session["csrf_token"]}


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "id_user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    @login_required
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            return halaman_error("Halaman ini khusus admin.", 403)
        return f(*args, **kwargs)
    return wrapper


# =========================
# ERROR HANDLER
# =========================

@app.errorhandler(mysql.connector.Error)
def handle_db_error(e):
    app.logger.exception("Database error: %s", e)
    return halaman_error("Terjadi kesalahan pada database. "
                        "Silakan coba lagi.", 500, str(e), petunjuk_db(e))


@app.errorhandler(400)
def handle_400(e):
    return halaman_error("Halaman ini sudah kedaluwarsa atau sesi login "
                        "kamu habis. Muat ulang halaman lalu coba lagi.",
                        400, getattr(e, "description", None))


@app.errorhandler(403)
def handle_403(e):
    return halaman_error("Akses ditolak.", 403)


@app.errorhandler(404)
def handle_404(e):
    return halaman_error("Halaman tidak ditemukan.", 404)


@app.errorhandler(500)
def handle_500(e):
    return halaman_error("Terjadi kesalahan pada server.", 500)


# =========================
# HOME, LOGIN, LOGOUT, REGISTER
# =========================

@app.route("/")
def home():
    return redirect("/hotel")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    ip = request.remote_addr or "?"

    if terlalu_banyak_gagal(ip):
        pesan = ("Terlalu banyak percobaan login gagal. "
                "Tunggu beberapa menit.")
        if app.debug:
            pesan += " [debug: restart server untuk langsung membukanya]"
        flash(pesan, "error")
        return redirect("/login")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    user = fetch_one("SELECT * FROM users WHERE username = %s", (username,))

    valid = bool(user) and password_cocok(user["password"], password)

    if not valid:
        catat_gagal(ip)
        pesan = "Username atau password salah."
        if app.debug:
            pesan += (f" [debug: username '{username}' tidak ada]"
                    if user is None else
                    " [debug: username ada, tapi password tidak cocok]")
        flash(pesan, "error")
        return redirect("/login")

    GAGAL_LOGIN.pop(ip, None)

    # Password lama (plain text) otomatis di-upgrade jadi hash
    if not (user["password"] or "").startswith(SUDAH_HASH):
        try:
            execute_write(
                "UPDATE users SET password = %s WHERE id_user = %s",
                (generate_password_hash(password), user["id_user"])
            )
        except mysql.connector.Error:
            app.logger.warning("Gagal upgrade hash password user %s.",
                            user["id_user"])

    session.clear()  # cegah session fixation
    session.permanent = True
    session["id_user"] = user["id_user"]
    session["nama"] = user["nama"]
    session["role"] = user["role"]

    return redirect("/admin" if user["role"] == "admin" else "/hotel")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    nama = request.form.get("nama", "").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not nama or not username or not password:
        flash("Semua field wajib diisi.", "error")
    elif len(nama) > 100:
        flash("Nama maksimal 100 karakter.", "error")
    elif not USERNAME_RE.match(username):
        flash("Username 3-50 karakter: huruf, angka, titik, garis bawah, "
            "atau strip.", "error")
    elif len(password) < 6:
        flash("Password minimal 6 karakter.", "error")
    else:
        try:
            execute_write(
                "INSERT INTO users (nama, username, password, role) "
                "VALUES (%s, %s, %s, %s)",
                (nama, username, generate_password_hash(password),
                ROLE_CUSTOMER)
            )
        except mysql.connector.IntegrityError:
            flash("Username sudah dipakai.", "error")
            return redirect("/register")

        flash("Pendaftaran berhasil. Silakan login.", "ok")
        return redirect("/login")

    return redirect("/register")


# =========================
# KAMAR
# =========================

@app.route("/rooms")
def rooms_json():
    return jsonify(to_jsonable(fetch_all("SELECT * FROM rooms")))


@app.route("/hotel")
@login_required
def hotel():
    return render_template(
        "rooms.html",
        rooms=fetch_all("SELECT * FROM rooms ORDER BY nomor_kamar")
    )


# =========================
# BOOKING
# =========================

@app.route("/bookings/<int:id_room>", methods=["GET", "POST"])
@login_required
def booking(id_room):

    room = fetch_one("SELECT * FROM rooms WHERE id_room = %s", (id_room,))

    if room is None:
        return halaman_error("Kamar tidak ditemukan.", 404)

    if str(room["status"]).strip().lower() != KAMAR_TERSEDIA.lower():
        flash("Kamar ini sedang tidak tersedia.", "error")
        return redirect("/hotel")

    addons = fetch_all("SELECT * FROM addons ORDER BY nama_addon")

    if request.method == "GET":
        return render_template("booking.html", room=room, addons=addons)

    # ---------- POST ----------
    balik = f"/bookings/{id_room}"

    tanggal_checkin = request.form.get("tanggal_checkin", "")
    tanggal_checkout = request.form.get("tanggal_checkout", "")

    try:
        checkin = datetime.strptime(tanggal_checkin, "%Y-%m-%d").date()
        checkout = datetime.strptime(tanggal_checkout, "%Y-%m-%d").date()
    except ValueError:
        flash("Format tanggal tidak valid.", "error")
        return redirect(balik)

    if checkin < date.today():
        flash("Tanggal check-in tidak boleh di masa lalu.", "error")
        return redirect(balik)

    jumlah_malam = (checkout - checkin).days

    if jumlah_malam <= 0:
        flash("Tanggal check-out harus setelah check-in.", "error")
        return redirect(balik)

    if jumlah_malam > MAX_MALAM:
        flash(f"Maksimal menginap {MAX_MALAM} malam.", "error")
        return redirect(balik)

    id_addon_dipilih = {
        int(a) for a in request.form.getlist("addons")
        if a.isdigit() and len(a) < 10
    }

    addons_dipilih = []
    if id_addon_dipilih:
        marks = ",".join(["%s"] * len(id_addon_dipilih))
        addons_dipilih = fetch_all(
            f"SELECT * FROM addons WHERE id_addon IN ({marks})",
            tuple(id_addon_dipilih)
        )

    total_harga = jumlah_malam * room["harga_per_malam"]
    for a in addons_dipilih:
        total_harga += a["harga"]

    with transaksi() as cur:
        # Kunci baris kamar agar dua booking bersamaan tidak bentrok
        cur.execute("SELECT id_room FROM rooms WHERE id_room = %s" + LOCK,
                    (id_room,))
        cur.fetchall()

        cur.execute(
            "SELECT 1 AS bentrok FROM bookings "
            "WHERE id_room = %s AND LOWER(status) <> %s "
            "AND tanggal_checkin < %s AND tanggal_checkout > %s LIMIT 1"
            + LOCK,
            (id_room, STATUS_BATAL, tanggal_checkout, tanggal_checkin)
        )
        bentrok = bool(cur.fetchall())

        if not bentrok:
            cur.execute("""
                INSERT INTO bookings
                    (id_user, id_room, tanggal_checkin, tanggal_checkout,
                    total_harga, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (session["id_user"], id_room, tanggal_checkin,
                tanggal_checkout, total_harga, STATUS_MENUNGGU))
            id_booking = cur.lastrowid

            for a in addons_dipilih:
                cur.execute(
                    "INSERT INTO booking_addons (id_booking, id_addon) "
                    "VALUES (%s, %s)", (id_booking, a["id_addon"])
                )

    if bentrok:
        flash("Kamar sudah dibooking pada tanggal tersebut.", "error")
        return redirect(balik)

    flash("Booking berhasil dibuat. Silakan lakukan pembayaran.", "ok")
    return redirect("/riwayat")


@app.route("/riwayat")
@login_required
def riwayat():
    query = """
        SELECT bookings.id_booking, bookings.id_user, users.nama,
            rooms.nomor_kamar, rooms.tipe_kamar,
            bookings.tanggal_checkin, bookings.tanggal_checkout,
            bookings.total_harga, bookings.status
        FROM bookings
        JOIN users ON bookings.id_user = users.id_user
        JOIN rooms ON bookings.id_room = rooms.id_room
    """

    if session.get("role") == "admin":
        data = fetch_all(query + " ORDER BY bookings.id_booking DESC")
    else:
        data = fetch_all(
            query + " WHERE bookings.id_user = %s "
                    "ORDER BY bookings.id_booking DESC",
            (session["id_user"],)
        )

    return render_template("bookings.html", bookings=data)


# =========================
# PEMBAYARAN & PEMBATALAN
# =========================

@app.route("/bayar/<int:id_booking>", methods=["GET", "POST"])
@login_required
def bayar(id_booking):

    data = fetch_one("""
        SELECT bookings.*, users.nama, rooms.nomor_kamar, rooms.tipe_kamar
        FROM bookings
        JOIN users ON bookings.id_user = users.id_user
        JOIN rooms ON bookings.id_room = rooms.id_room
        WHERE bookings.id_booking = %s
    """, (id_booking,))

    if data is None:
        return halaman_error("Booking tidak ditemukan.", 404)

    if (session.get("role") != "admin"
            and data["id_user"] != session["id_user"]):
        return halaman_error("Akses ditolak.", 403)

    status = str(data["status"]).lower()

    if status == STATUS_LUNAS:
        return redirect("/riwayat")

    if status == STATUS_BATAL:
        flash("Booking ini sudah dibatalkan.", "error")
        return redirect("/riwayat")

    if request.method == "POST":
        execute_write(
            "UPDATE bookings SET status = %s "
            "WHERE id_booking = %s AND LOWER(status) NOT IN (%s, %s)",
            (STATUS_LUNAS, id_booking, STATUS_LUNAS, STATUS_BATAL)
        )
        flash("Pembayaran berhasil.", "ok")
        return redirect("/riwayat")

    return render_template("payment.html", booking=data)


@app.route("/batal/<int:id_booking>", methods=["POST"])
@login_required
def batal(id_booking):

    data = fetch_one(
        "SELECT id_user, status FROM bookings WHERE id_booking = %s",
        (id_booking,)
    )

    if data is None:
        return halaman_error("Booking tidak ditemukan.", 404)

    admin = session.get("role") == "admin"

    if not admin and data["id_user"] != session["id_user"]:
        return halaman_error("Akses ditolak.", 403)

    status = str(data["status"]).lower()

    if status == STATUS_BATAL:
        flash("Booking sudah dibatalkan sebelumnya.", "error")
    elif status == STATUS_LUNAS and not admin:
        flash("Booking yang sudah lunas hanya bisa dibatalkan oleh admin.",
            "error")
    else:
        execute_write(
            "UPDATE bookings SET status = %s WHERE id_booking = %s",
            (STATUS_BATAL, id_booking)
        )
        flash("Booking dibatalkan.", "ok")

    return redirect("/riwayat")


# =========================
# ADMIN
# =========================

@app.route("/admin")
@admin_required
def admin():
    return render_template(
        "admin.html",
        rooms=fetch_all("SELECT * FROM rooms ORDER BY nomor_kamar"),
        users=fetch_all("SELECT id_user, nama, username, role FROM users"),
        bookings=fetch_all("""
            SELECT bookings.*, users.nama, rooms.nomor_kamar
            FROM bookings
            JOIN users ON bookings.id_user = users.id_user
            JOIN rooms ON bookings.id_room = rooms.id_room
            ORDER BY bookings.id_booking DESC
        """),
        addons=fetch_all("SELECT * FROM addons ORDER BY nama_addon"),
    )


@app.route("/admin/kamar/tambah", methods=["POST"])
@admin_required
def admin_tambah_kamar():
    nomor = request.form.get("nomor_kamar", "").strip()
    tipe = request.form.get("tipe_kamar", "").strip()
    harga = parse_harga(request.form.get("harga_per_malam"))

    if not nomor or not tipe or len(nomor) > 10 or len(tipe) > 50 \
            or harga is None:
        flash("Data kamar tidak valid.", "error")
    else:
        try:
            execute_write(
                "INSERT INTO rooms (nomor_kamar, tipe_kamar, "
                "harga_per_malam, status) VALUES (%s, %s, %s, %s)",
                (nomor, tipe, harga, KAMAR_TERSEDIA)
            )
            flash("Kamar ditambahkan.", "ok")
        except mysql.connector.IntegrityError:
            flash("Nomor kamar sudah ada.", "error")

    return redirect("/admin")


@app.route("/admin/kamar/<int:id_room>/status", methods=["POST"])
@admin_required
def admin_status_kamar(id_room):
    baru = request.form.get("status")

    if baru not in (KAMAR_TERSEDIA, KAMAR_TIDAK):
        abort(400)

    execute_write("UPDATE rooms SET status = %s WHERE id_room = %s",
                (baru, id_room))
    flash("Status kamar diperbarui.", "ok")
    return redirect("/admin")


@app.route("/admin/addon/tambah", methods=["POST"])
@admin_required
def admin_tambah_addon():
    nama = request.form.get("nama_addon", "").strip()
    harga = parse_harga(request.form.get("harga"))

    if not nama or len(nama) > 100 or harga is None:
        flash("Data add-on tidak valid.", "error")
    else:
        execute_write(
            "INSERT INTO addons (nama_addon, harga) VALUES (%s, %s)",
            (nama, harga)
        )
        flash("Add-on ditambahkan.", "ok")

    return redirect("/admin")


# =========================
# CLI
# =========================

def buat_admin(username, password, nama):
    """Buat admin baru, atau reset password + jadikan admin kalau ada."""
    if not USERNAME_RE.match(username) or len(password) < 6:
        print("Username 3-50 karakter (huruf/angka/._-), password min 6.")
        return 1

    try:
        db = koneksi()
        cur = db.cursor()
        hashed = generate_password_hash(password)
        cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if cur.fetchall():
            cur.execute("UPDATE users SET password = %s, role = 'admin' "
                        "WHERE username = %s", (hashed, username))
            print(f"Akun '{username}' di-reset dan dijadikan admin.")
        else:
            cur.execute("INSERT INTO users (nama, username, password, role) "
                        "VALUES (%s, %s, %s, 'admin')",
                        (nama, username, hashed))
            print(f"Admin '{username}' dibuat.")
        db.close()
    except mysql.connector.Error as e:
        print(f"[MASALAH] Gagal menulis ke database: {e}")
        return 1
    return 0


def cek_user(username, password=None):
    """Periksa akun langsung ke database, tanpa browser."""
    try:
        db = koneksi()
        cur = db.cursor(dictionary=True, buffered=True)
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.execute("SELECT username, role FROM users LIMIT 30")
        semua = cur.fetchall()
        db.close()
    except mysql.connector.Error as e:
        print(f"[MASALAH] Tidak bisa membaca database: {e}")
        return 1

    if user is None:
        print(f"[MASALAH] Username '{username}' tidak ada.")
        print("Username yang ada:",
            ", ".join(f"{u['username']} ({u['role']})" for u in semua)
            or "(tabel users kosong)")
        return 1

    tersimpan = user.get("password") or ""
    bentuk = "hash" if tersimpan.startswith(SUDAH_HASH) else "plain text"
    print(f"[OK] '{username}' ditemukan. Role: {user.get('role')}. "
        f"Password tersimpan sebagai: {bentuk}.")

    if password is None:
        return 0
    if password_cocok(tersimpan, password):
        print("[OK] Password COCOK.")
        return 0
    print("[MASALAH] Password TIDAK cocok. Reset dengan: "
        f"python app.py buat-admin {username} PASSWORDBARU")
    return 1


# =========================
# RUN
# =========================

# Saat mode debug, proses induk reloader tidak perlu menyiapkan database
# (prosesnya diulang oleh proses anak), supaya pesan tidak tampil dua kali.
if not (DEBUG and __name__ == "__main__"
        and os.environ.get("WERKZEUG_RUN_MAIN") != "true"):
    periksa_template()
    init_db()

if __name__ == "__main__":
    # python app.py cek-user USERNAME [PASSWORD]
    if len(sys.argv) >= 3 and sys.argv[1] == "cek-user":
        sys.exit(cek_user(sys.argv[2],
                        sys.argv[3] if len(sys.argv) > 3 else None))

    # python app.py buat-admin USERNAME PASSWORD ["Nama Lengkap"]
    if len(sys.argv) >= 4 and sys.argv[1] == "buat-admin":
        sys.exit(buat_admin(sys.argv[2], sys.argv[3],
                            sys.argv[4] if len(sys.argv) > 4
                            else "Administrator"))

    app.run(debug=DEBUG)
