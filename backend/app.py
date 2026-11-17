import os
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from functools import wraps

import mysql.connector
from flask import (Flask, abort, flash, g, jsonify, redirect,
                render_template, request, session)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "ganti-dengan-kunci-rahasia-kamu"
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# --- pengaturan API untuk frontend React ---
# Alamat frontend yang boleh memanggil /api (pisahkan dengan koma).
CORS_ORIGINS = [o.strip() for o in os.environ.get(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")]
HOLD_JAM = 2          # batas waktu bayar (sama dengan HOLD_MS di frontend)
MAKS_MALAM = 60       # batas lama menginap per booking
MAKS_TAMU = 20
BANK_VALID = ("BCA", "MANDIRI", "BNI")
STATUS_API = {"menunggu": "pending", "lunas": "paid", "batal": "cancelled"}

DB = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "hotel",
}


# ---------- database ----------

def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(autocommit=True, **DB)
    return g.db


@app.teardown_appcontext
def tutup_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def ambil_semua(sql, params=()):
    cur = get_db().cursor(dictionary=True, buffered=True)
    cur.execute(sql, params)
    hasil = cur.fetchall()
    cur.close()
    return hasil


def ambil_satu(sql, params=()):
    cur = get_db().cursor(dictionary=True, buffered=True)
    cur.execute(sql, params)
    hasil = cur.fetchone()
    cur.close()
    return hasil


def jalankan(sql, params=()):
    cur = get_db().cursor(buffered=True)
    cur.execute(sql, params)
    id_baru = cur.lastrowid
    cur.close()
    return id_baru


def ubah(sql, params=()):
    """Jalankan UPDATE/DELETE dan kembalikan jumlah baris yang berubah."""
    cur = get_db().cursor(buffered=True)
    cur.execute(sql, params)
    jumlah = cur.rowcount
    cur.close()
    return jumlah


# ---------- helper ----------

@app.template_filter("rupiah")
def rupiah(nilai):
    try:
        return "Rp" + f"{int(nilai):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "Rp0"


def halaman_error(pesan, kode=400):
    return render_template("error.html", pesan=pesan, kode=kode,
                        petunjuk=None, detail=None), kode


@app.context_processor
def kirim_csrf():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return {"csrf_token": session["csrf_token"]}


@app.before_request
def cek_csrf():
    if request.method == "POST" and not request.path.startswith("/api/"):
        if session.get("csrf_token") != request.form.get("csrf_token"):
            abort(400)


def harus_login(f):
    @wraps(f)
    def bungkus(*args, **kwargs):
        if "id_user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return bungkus


def harus_admin(f):
    @wraps(f)
    @harus_login
    def bungkus(*args, **kwargs):
        if session.get("role") != "admin":
            return halaman_error("Halaman ini khusus admin.", 403)
        return f(*args, **kwargs)
    return bungkus


@app.errorhandler(400)
def error_400(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Bad request."}), 400
    return halaman_error("Halaman kedaluwarsa. Muat ulang lalu coba lagi.", 400)


@app.errorhandler(404)
def error_404(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found."}), 404
    return halaman_error("Halaman tidak ditemukan.", 404)


# ---------- login, register ----------

@app.route("/")
def home():
    return redirect("/hotel")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    user = ambil_satu("SELECT * FROM users WHERE username = %s", (username,))

    if user is None or not check_password_hash(user["password"], password):
        flash("Username atau password salah.", "error")
        return redirect("/login")

    session.clear()
    session["id_user"] = user["id_user"]
    session["nama"] = user["nama"]
    session["role"] = user["role"]

    if user["role"] == "admin":
        return redirect("/admin")
    return redirect("/hotel")


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
        return redirect("/register")

    if len(password) < 6:
        flash("Password minimal 6 karakter.", "error")
        return redirect("/register")

    ada = ambil_satu("SELECT 1 AS x FROM users WHERE username = %s", (username,))
    if ada:
        flash("Username sudah dipakai.", "error")
        return redirect("/register")

    jalankan(
        "INSERT INTO users (nama, username, password, role) "
        "VALUES (%s, %s, %s, 'customer')",
        (nama, username, generate_password_hash(password)),
    )
    flash("Pendaftaran berhasil. Silakan login.", "ok")
    return redirect("/login")


# ---------- kamar ----------

@app.route("/rooms")
def rooms_json():
    rooms = ambil_semua("SELECT * FROM rooms")
    for r in rooms:
        r["harga_per_malam"] = float(r["harga_per_malam"])
    return jsonify(rooms)


@app.route("/hotel")
@harus_login
def hotel():
    if session["role"] == "admin":
        return redirect("/admin")

    rooms = ambil_semua("SELECT * FROM rooms ORDER BY nomor_kamar")
    return render_template("rooms.html", rooms=rooms)


# ---------- booking ----------

@app.route("/bookings/<int:id_room>", methods=["GET", "POST"])
@harus_login
def booking(id_room):
    if session["role"] == "admin":
        flash("Admin tidak bisa memesan kamar.", "error")
        return redirect("/admin")

    room = ambil_satu("SELECT * FROM rooms WHERE id_room = %s", (id_room,))
    if room is None:
        return halaman_error("Kamar tidak ditemukan.", 404)

    if room["status"].lower() != "tersedia":
        flash("Kamar ini sedang tidak tersedia.", "error")
        return redirect("/hotel")

    addons = ambil_semua("SELECT * FROM addons ORDER BY nama_addon")

    if request.method == "GET":
        return render_template("booking.html", room=room, addons=addons)

    balik = f"/bookings/{id_room}"
    tgl_masuk = request.form.get("tanggal_checkin", "")
    tgl_keluar = request.form.get("tanggal_checkout", "")

    try:
        masuk = datetime.strptime(tgl_masuk, "%Y-%m-%d").date()
        keluar = datetime.strptime(tgl_keluar, "%Y-%m-%d").date()
    except ValueError:
        flash("Format tanggal tidak valid.", "error")
        return redirect(balik)

    if masuk < date.today():
        flash("Tanggal check-in tidak boleh di masa lalu.", "error")
        return redirect(balik)

    malam = (keluar - masuk).days
    if malam <= 0:
        flash("Tanggal check-out harus setelah check-in.", "error")
        return redirect(balik)

    # cek apakah kamar sudah dipesan di tanggal itu
    bentrok = ambil_satu(
        "SELECT 1 AS x FROM bookings "
        "WHERE id_room = %s AND LOWER(status) <> 'batal' "
        "AND tanggal_checkin < %s AND tanggal_checkout > %s LIMIT 1",
        (id_room, tgl_keluar, tgl_masuk),
    )
    if bentrok:
        flash("Kamar sudah dibooking pada tanggal tersebut.", "error")
        return redirect(balik)

    # hitung total harga
    total = malam * room["harga_per_malam"]
    addon_dipilih = []
    for id_addon in request.form.getlist("addons"):
        if not id_addon.isdigit():
            continue
        a = ambil_satu("SELECT * FROM addons WHERE id_addon = %s", (id_addon,))
        if a:
            addon_dipilih.append(a)
            total += a["harga"]

    id_booking = jalankan(
        "INSERT INTO bookings (id_user, id_room, tanggal_checkin, "
        "tanggal_checkout, total_harga, status) "
        "VALUES (%s, %s, %s, %s, %s, 'Menunggu')",
        (session["id_user"], id_room, tgl_masuk, tgl_keluar, total),
    )
    for a in addon_dipilih:
        jalankan("INSERT INTO booking_addons (id_booking, id_addon) "
            "VALUES (%s, %s)", (id_booking, a["id_addon"]))

    flash("Booking berhasil dibuat. Silakan lakukan pembayaran.", "ok")
    return redirect(f"/bayar/{id_booking}")


@app.route("/riwayat")
@harus_login
def riwayat():
    sql = """
        SELECT bookings.*, users.nama, rooms.nomor_kamar, rooms.tipe_kamar
        FROM bookings
        JOIN users ON bookings.id_user = users.id_user
        JOIN rooms ON bookings.id_room = rooms.id_room
    """
    if session["role"] == "admin":
        data = ambil_semua(sql + " ORDER BY bookings.id_booking DESC")
    else:
        data = ambil_semua(
            sql + " WHERE bookings.id_user = %s "
                "ORDER BY bookings.id_booking DESC",
            (session["id_user"],),
        )
    return render_template("bookings.html", bookings=data)


# ---------- pembayaran & pembatalan ----------

@app.route("/bayar/<int:id_booking>", methods=["GET", "POST"])
@harus_login
def bayar(id_booking):
    data = ambil_satu("""
        SELECT bookings.*, users.nama, rooms.nomor_kamar, rooms.tipe_kamar
        FROM bookings
        JOIN users ON bookings.id_user = users.id_user
        JOIN rooms ON bookings.id_room = rooms.id_room
        WHERE bookings.id_booking = %s
    """, (id_booking,))

    if data is None:
        return halaman_error("Booking tidak ditemukan.", 404)

    if session["role"] != "admin" and data["id_user"] != session["id_user"]:
        return halaman_error("Akses ditolak.", 403)

    status = data["status"].lower()
    if status == "lunas":
        return redirect("/riwayat")
    if status == "batal":
        flash("Booking ini sudah dibatalkan.", "error")
        return redirect("/riwayat")

    if request.method == "POST":
        jalankan("UPDATE bookings SET status = 'lunas' WHERE id_booking = %s",
                (id_booking,))
        flash("Pembayaran berhasil.", "ok")
        return redirect("/riwayat")

    return render_template("payment.html", booking=data)


@app.route("/batal/<int:id_booking>", methods=["POST"])
@harus_login
def batal(id_booking):
    data = ambil_satu(
        "SELECT id_user, status FROM bookings WHERE id_booking = %s",
        (id_booking,),
    )
    if data is None:
        return halaman_error("Booking tidak ditemukan.", 404)

    admin = session["role"] == "admin"
    if not admin and data["id_user"] != session["id_user"]:
        return halaman_error("Akses ditolak.", 403)

    status = data["status"].lower()
    if status == "batal":
        flash("Booking sudah dibatalkan sebelumnya.", "error")
    elif status == "lunas" and not admin:
        flash("Booking yang sudah lunas hanya bisa dibatalkan oleh admin.",
            "error")
    else:
        jalankan("UPDATE bookings SET status = 'batal' WHERE id_booking = %s",
                (id_booking,))
        flash("Booking dibatalkan.", "ok")

    return redirect("/riwayat")


# ---------- admin ----------

@app.route("/admin")
@harus_admin
def admin():
    return render_template(
        "admin.html",
        rooms=ambil_semua("SELECT * FROM rooms ORDER BY nomor_kamar"),
        users=ambil_semua("SELECT id_user, nama, username, role FROM users"),
        bookings=ambil_semua("""
            SELECT bookings.*, users.nama, rooms.nomor_kamar
            FROM bookings
            JOIN users ON bookings.id_user = users.id_user
            JOIN rooms ON bookings.id_room = rooms.id_room
            ORDER BY bookings.id_booking DESC
        """),
        addons=ambil_semua("SELECT * FROM addons ORDER BY nama_addon"),
    )


@app.route("/admin/kamar/tambah", methods=["POST"])
@harus_admin
def tambah_kamar():
    nomor = request.form.get("nomor_kamar", "").strip()
    tipe = request.form.get("tipe_kamar", "").strip()
    harga = request.form.get("harga_per_malam", "").strip()
    kapasitas = request.form.get("kapasitas", "").strip()

    if (not nomor or not tipe or not harga.isdigit() or int(harga) <= 0
            or not kapasitas.isdigit() or int(kapasitas) < 1):
        flash("Data kamar tidak valid.", "error")
        return redirect("/admin")

    ada = ambil_satu("SELECT 1 AS x FROM rooms WHERE nomor_kamar = %s", (nomor,))
    if ada:
        flash("Nomor kamar sudah ada.", "error")
        return redirect("/admin")

    jalankan("INSERT INTO rooms (nomor_kamar, tipe_kamar, harga_per_malam, "
            "kapasitas, status) VALUES (%s, %s, %s, %s, 'Tersedia')",
            (nomor, tipe, harga, kapasitas))
    flash("Kamar ditambahkan.", "ok")
    return redirect("/admin")


@app.route("/admin/kamar/<int:id_room>/status", methods=["POST"])
@harus_admin
def status_kamar(id_room):
    baru = request.form.get("status")
    if baru not in ("Tersedia", "Tidak Tersedia"):
        abort(400)

    jalankan("UPDATE rooms SET status = %s WHERE id_room = %s",
            (baru, id_room))
    flash("Status kamar diperbarui.", "ok")
    return redirect("/admin")


@app.route("/admin/addon/tambah", methods=["POST"])
@harus_admin
def tambah_addon():
    nama = request.form.get("nama_addon", "").strip()
    harga = request.form.get("harga", "").strip()

    if not nama or not harga.isdigit() or int(harga) <= 0:
        flash("Data add-on tidak valid.", "error")
        return redirect("/admin")

    jalankan("INSERT INTO addons (nama_addon, harga) VALUES (%s, %s)",
            (nama, harga))
    flash("Add-on ditambahkan.", "ok")
    return redirect("/admin")


# =====================================================================
# API JSON untuk frontend React (alamat berawalan /api)
# Bentuk data mengikuti komentar "FLASK:" di frontend/src/data/bookingservice.js
# Halaman HTML lama (Jinja) di atas tetap berjalan seperti biasa.
# =====================================================================

def sekarang_utc():
    # waktu kedaluwarsa disimpan sebagai UTC polos agar tidak bergantung zona server
    return datetime.now(timezone.utc).replace(tzinfo=None)


def ke_ms(waktu):
    return int(waktu.replace(tzinfo=timezone.utc).timestamp() * 1000)


def buat_ref(id_booking):
    return f"BK{id_booking:04d}"


def baca_ref(ref):
    cocok = re.fullmatch(r"BK(\d{1,9})", str(ref).upper(), re.ASCII)
    return int(cocok.group(1)) if cocok else None


def api_error(pesan, kode):
    return jsonify({"error": pesan}), kode


@app.before_request
def jaga_api():
    """Perlindungan CSRF untuk /api: asal request harus dikenal dan POST harus JSON."""
    if not request.path.startswith("/api/") or request.method in ("GET", "HEAD", "OPTIONS"):
        return
    asal = request.headers.get("Origin")
    if asal and asal not in CORS_ORIGINS and asal != request.host_url.rstrip("/"):
        return api_error("Origin not allowed.", 403)
    if request.method == "POST" and not request.is_json:
        return api_error("Content-Type must be application/json.", 415)


@app.before_request
def kedaluwarsakan_booking():
    """Booking 'Menunggu' yang lewat batas bayar otomatis dibatalkan (kamar kosong lagi)."""
    if request.endpoint in (None, "static") or request.method == "OPTIONS":
        return
    jalankan("UPDATE bookings SET status = 'batal' "
            "WHERE LOWER(status) = 'menunggu' "
            "AND expires_at IS NOT NULL AND expires_at < %s", (sekarang_utc(),))


@app.after_request
def pasang_cors(resp):
    asal = request.headers.get("Origin")
    if request.path.startswith("/api/") and asal in CORS_ORIGINS:
        resp.headers["Access-Control-Allow-Origin"] = asal
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, OPTIONS"
        resp.headers["Vary"] = "Origin"
    return resp


def api_harus_login(f):
    @wraps(f)
    def bungkus(*args, **kwargs):
        if "id_user" not in session:
            return api_error("Please sign in first.", 401)
        return f(*args, **kwargs)
    return bungkus


def teks(data, kunci):
    nilai = data.get(kunci) if isinstance(data, dict) else None
    return nilai.strip() if isinstance(nilai, str) else ""


def data_user(u):
    return {"id": u["id_user"], "name": u["nama"],
            "username": u["username"], "role": u["role"]}


# ---------- akun ----------

@app.route("/api/me")
def api_me():
    if "id_user" not in session:
        return jsonify({"loggedIn": False})
    u = ambil_satu("SELECT id_user, nama, username, role FROM users "
                "WHERE id_user = %s", (session["id_user"],))
    if u is None:
        session.clear()
        return jsonify({"loggedIn": False})
    return jsonify({"loggedIn": True, "user": data_user(u)})


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True)
    username = teks(data, "username")
    email = teks(data, "email").lower()
    password = data.get("password") if isinstance(data, dict) else None

    if not username or len(username) > 50:
        return api_error("Username is required (max 50 characters).", 400)
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 100:
        return api_error("Please enter a valid email address.", 400)
    if not isinstance(password, str) or not 6 <= len(password) <= 128:
        return api_error("Password must be 6 to 128 characters.", 400)

    if ambil_satu("SELECT 1 AS x FROM users WHERE username = %s", (username,)):
        return api_error("Username is already taken.", 409)
    if ambil_satu("SELECT 1 AS x FROM users WHERE email = %s", (email,)):
        return api_error("Email is already registered.", 409)

    try:
        id_user = jalankan(
            "INSERT INTO users (nama, username, email, password, role) "
            "VALUES (%s, %s, %s, %s, 'customer')",
            (username, username, email, generate_password_hash(password)),
        )
    except mysql.connector.IntegrityError:   # dua orang daftar bersamaan
        return api_error("Username or email is already registered.", 409)
    return jsonify({"user": {"id": id_user, "name": username,
                            "username": username, "role": "customer"}}), 201


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True)
    username = teks(data, "username")
    password = data.get("password") if isinstance(data, dict) else None

    user = ambil_satu("SELECT * FROM users WHERE username = %s", (username,))
    if (user is None or not isinstance(password, str)
            or not check_password_hash(user["password"], password)):
        return api_error("Invalid username or password.", 401)

    session.clear()
    session["id_user"] = user["id_user"]
    session["nama"] = user["nama"]
    session["role"] = user["role"]
    return jsonify({"user": data_user(user)})


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True})


# ---------- data publik ----------

@app.route("/api/experiences")
def api_experiences():
    rows = ambil_semua("SELECT * FROM addons ORDER BY id_addon")
    return jsonify([{
        "id": a["id_addon"],
        "tab": a["nama_addon"],
        "title": a["nama_addon"],
        "image": a.get("gambar"),
        "price": int(a["harga"]),
        "description": a.get("deskripsi"),
    } for a in rows])


def cek_tanggal_api(tgl_masuk, tgl_keluar):
    """Kembalikan (masuk_iso, keluar_iso, jumlah_malam, pesan_error)."""
    try:
        masuk = datetime.strptime(tgl_masuk, "%Y-%m-%d").date()
        keluar = datetime.strptime(tgl_keluar, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None, None, 0, "Dates must use the YYYY-MM-DD format."
    if masuk < date.today():
        return None, None, 0, "Check-in cannot be in the past."
    malam = (keluar - masuk).days
    if malam <= 0:
        return None, None, 0, "Check-out must be after check-in."
    if malam > MAKS_MALAM:
        return None, None, 0, f"Stays are limited to {MAKS_MALAM} nights."
    return masuk.isoformat(), keluar.isoformat(), malam, None


def cek_tamu_api(nilai):
    if isinstance(nilai, bool):
        return 0, "Guests must be a whole number."
    if isinstance(nilai, str) and re.fullmatch(r"[0-9]{1,3}", nilai):
        nilai = int(nilai)
    if not isinstance(nilai, int) or not 1 <= nilai <= MAKS_TAMU:
        return 0, f"Guests must be between 1 and {MAKS_TAMU}."
    return nilai, None


def kamar_bentrok(id_room, tgl_masuk, tgl_keluar):
    return ambil_satu(
        "SELECT 1 AS x FROM bookings "
        "WHERE id_room = %s AND LOWER(status) <> 'batal' "
        "AND tanggal_checkin < %s AND tanggal_checkout > %s LIMIT 1",
        (id_room, tgl_keluar, tgl_masuk),
    )


@app.route("/api/rooms/availability")
def api_ketersediaan():
    masuk, keluar, _, error = cek_tanggal_api(
        request.args.get("check_in", ""), request.args.get("check_out", ""))
    if error:
        return api_error(error, 400)
    tamu, error = cek_tamu_api(request.args.get("guests", ""))
    if error:
        return api_error(error, 400)

    # hanya kamar fisik yang aktif, muat untuk jumlah tamu, dan tidak bentrok
    rows = ambil_semua(
        "SELECT r.tipe_kamar, r.harga_per_malam, r.kapasitas "
        "FROM rooms r "
        "WHERE LOWER(r.status) = 'tersedia' AND r.kapasitas >= %s "
        "AND NOT EXISTS ("
        "  SELECT 1 FROM bookings b "
        "  WHERE b.id_room = r.id_room AND LOWER(b.status) <> 'batal' "
        "  AND b.tanggal_checkin < %s AND b.tanggal_checkout > %s) "
        "ORDER BY r.harga_per_malam, r.nomor_kamar",
        (tamu, keluar, masuk),
    )
    # beberapa kamar fisik bertipe sama digabung jadi satu pilihan tipe
    tipe = {}
    for r in rows:
        t = tipe.setdefault(r["tipe_kamar"], {
            "id": r["tipe_kamar"], "name": r["tipe_kamar"],
            "price": int(r["harga_per_malam"]),    # baris terurut: yang pertama termurah
            "capacity": r["kapasitas"], "available": True})
        t["capacity"] = max(t["capacity"], r["kapasitas"])
    return jsonify(sorted(tipe.values(), key=lambda t: (t["price"], t["name"])))


# ---------- booking ----------

def buat_va():
    angka = "8077" + "".join(str(secrets.randbelow(10)) for _ in range(12))
    return " ".join(angka[i:i + 4] for i in range(0, 16, 4))


def data_booking(b):
    addon = ambil_semua("SELECT id_addon FROM booking_addons "
                        "WHERE id_booking = %s ORDER BY id_addon", (b["id_booking"],))
    status = b["status"].lower()
    return {
        "ref": buat_ref(b["id_booking"]),
        "status": STATUS_API.get(status, status),
        "roomId": b["tipe_kamar"],
        "checkIn": str(b["tanggal_checkin"]),
        "checkOut": str(b["tanggal_checkout"]),
        "guests": b["jumlah_tamu"],
        "addonIds": [a["id_addon"] for a in addon],
        "bank": b["bank"],
        "vaNumber": b["va_number"],
        "total": int(b["total_harga"]),
        "expiresAt": ke_ms(b["expires_at"]) if b["expires_at"] else None,
    }


SQL_BOOKING = ("SELECT b.*, r.tipe_kamar FROM bookings b "
            "JOIN rooms r ON r.id_room = b.id_room ")


def booking_milik(ref):
    """Booking milik user yang login (admin boleh semua), atau None."""
    id_booking = baca_ref(ref)
    if id_booking is None:
        return None
    b = ambil_satu(SQL_BOOKING + "WHERE b.id_booking = %s", (id_booking,))
    if b is None:
        return None
    if session.get("role") != "admin" and b["id_user"] != session["id_user"]:
        return None
    return b


@app.route("/api/bookings", methods=["GET"])
@api_harus_login
def api_daftar_booking():
    rows = ambil_semua(SQL_BOOKING + "WHERE b.id_user = %s "
                    "ORDER BY b.id_booking DESC", (session["id_user"],))
    return jsonify([data_booking(b) for b in rows])


@app.route("/api/bookings/<ref>", methods=["GET"])
@api_harus_login
def api_detail_booking(ref):
    b = booking_milik(ref)
    if b is None:
        return api_error("Booking not found.", 404)
    return jsonify(data_booking(b))


@app.route("/api/bookings", methods=["POST"])
@api_harus_login
def api_buat_booking():
    if session["role"] == "admin":
        return api_error("Admins cannot make bookings.", 403)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return api_error("Invalid request body.", 400)

    masuk, keluar, malam, error = cek_tanggal_api(
        data.get("checkIn"), data.get("checkOut"))
    if error:
        return api_error(error, 400)
    tamu, error = cek_tamu_api(data.get("guests"))
    if error:
        return api_error(error, 400)

    tipe = data.get("roomId")
    if not isinstance(tipe, str) or not tipe:
        return api_error("Please choose a room.", 400)
    bank = data.get("bank")
    if bank not in BANK_VALID:
        return api_error("Please choose a valid bank.", 400)

    # add-on: id harus angka bulat dan ada di database (total dari frontend diabaikan)
    id_addon = data.get("addonIds", [])
    if (not isinstance(id_addon, list) or len(id_addon) > 50
            or not all(isinstance(i, int) and not isinstance(i, bool) and i > 0
                    for i in id_addon)):
        return api_error("Invalid experiences.", 400)
    id_addon = sorted(set(id_addon))
    harga_addon = 0
    if id_addon:
        marks = ",".join(["%s"] * len(id_addon))
        rows = ambil_semua(
            f"SELECT harga FROM addons WHERE id_addon IN ({marks})", tuple(id_addon))
        if len(rows) != len(id_addon):
            return api_error("One of the experiences does not exist.", 400)
        harga_addon = sum(int(r["harga"]) for r in rows)

    # Transaksi: kunci kamar bertipe ini supaya dua pemesan tidak mendapat kamar yang sama.
    # SELECT pertama di dalam transaksi adalah locking read, jadi pengecekan bentrok
    # sesudahnya selalu melihat booking yang baru saja di-commit orang lain.
    db = get_db()
    db.start_transaction()
    try:
        kandidat = ambil_semua(
            "SELECT id_room, harga_per_malam FROM rooms "
            "WHERE tipe_kamar = %s AND LOWER(status) = 'tersedia' AND kapasitas >= %s "
            "ORDER BY harga_per_malam, nomor_kamar FOR UPDATE", (tipe, tamu))
        kamar = next((k for k in kandidat
                    if not kamar_bentrok(k["id_room"], masuk, keluar)), None)
        if kamar is None:
            db.rollback()
            return api_error("This room is no longer available for the selected dates.", 409)

        total = malam * int(kamar["harga_per_malam"]) + harga_addon
        batas = sekarang_utc() + timedelta(hours=HOLD_JAM)
        va = buat_va()
        id_booking = jalankan(
            "INSERT INTO bookings (id_user, id_room, tanggal_checkin, "
            "tanggal_checkout, jumlah_tamu, total_harga, status, bank, "
            "va_number, expires_at) "
            "VALUES (%s, %s, %s, %s, %s, %s, 'Menunggu', %s, %s, %s)",
            (session["id_user"], kamar["id_room"], masuk, keluar, tamu,
            total, bank, va, batas))
        for i in id_addon:
            jalankan("INSERT INTO booking_addons (id_booking, id_addon) "
                    "VALUES (%s, %s)", (id_booking, i))
        db.commit()
    except Exception:
        db.rollback()
        raise

    b = ambil_satu(SQL_BOOKING + "WHERE b.id_booking = %s", (id_booking,))
    return jsonify(data_booking(b)), 201


@app.route("/api/bookings/<ref>/pay", methods=["PATCH"])
@api_harus_login
def api_bayar(ref):
    b = booking_milik(ref)
    if b is None:
        return api_error("Booking not found.", 404)
    kode = buat_ref(b["id_booking"])

    status = b["status"].lower()
    if status == "lunas":
        return jsonify({"ref": kode, "status": "paid"})
    if status == "batal":
        return api_error("This booking was cancelled or has expired.", 409)

    berubah = ubah(
        "UPDATE bookings SET status = 'lunas' WHERE id_booking = %s "
        "AND LOWER(status) = 'menunggu' "
        "AND (expires_at IS NULL OR expires_at >= %s)",
        (b["id_booking"], sekarang_utc()))
    if berubah == 0:
        return api_error("This booking has expired.", 409)
    return jsonify({"ref": kode, "status": "paid"})


@app.route("/api/bookings/<ref>/cancel", methods=["PATCH"])
@api_harus_login
def api_batal(ref):
    b = booking_milik(ref)
    if b is None:
        return api_error("Booking not found.", 404)
    kode = buat_ref(b["id_booking"])

    admin = session.get("role") == "admin"
    status = b["status"].lower()
    if status == "batal":
        return api_error("This booking is already cancelled.", 409)
    if status == "lunas" and not admin:
        return api_error("Paid bookings can only be cancelled by an admin.", 403)

    syarat = "LOWER(status) <> 'batal'" if admin else "LOWER(status) = 'menunggu'"
    berubah = ubah("UPDATE bookings SET status = 'batal' "
                f"WHERE id_booking = %s AND {syarat}", (b["id_booking"],))
    if berubah == 0:
        return api_error("This booking can no longer be cancelled.", 409)
    return jsonify({"ref": kode, "status": "cancelled"})


if __name__ == "__main__":
    app.run(debug=True)