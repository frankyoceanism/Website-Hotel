import secrets
from datetime import date, datetime
from functools import wraps

import mysql.connector
from flask import (Flask, abort, flash, g, jsonify, redirect,
                render_template, request, session)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "ganti-dengan-kunci-rahasia-kamu"

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
    if request.method == "POST":
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
    return halaman_error("Halaman kedaluwarsa. Muat ulang lalu coba lagi.", 400)


@app.errorhandler(404)
def error_404(e):
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

    if not nomor or not tipe or not harga.isdigit() or int(harga) <= 0:
        flash("Data kamar tidak valid.", "error")
        return redirect("/admin")

    ada = ambil_satu("SELECT 1 AS x FROM rooms WHERE nomor_kamar = %s", (nomor,))
    if ada:
        flash("Nomor kamar sudah ada.", "error")
        return redirect("/admin")

    jalankan("INSERT INTO rooms (nomor_kamar, tipe_kamar, harga_per_malam, "
            "status) VALUES (%s, %s, %s, 'Tersedia')", (nomor, tipe, harga))
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


if __name__ == "__main__":
    app.run(debug=True)