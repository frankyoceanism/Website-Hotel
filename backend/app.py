from flask import Flask, jsonify, request, render_template , session, redirect
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = "hotel-secret"

db = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "",
    database = "hotel"
)

@app.route("/")
def home():
    return " coba nyambung ngga?"

@app.route("/rooms")
def rooms():
    cursor = db.cursor(dictionary=True)
    cursor.execute("select * from rooms")
    data = cursor.fetchall()
    cursor.close()

    return jsonify(data)

@app.route("/hotel")
def hotel():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM rooms")
    rooms = cursor.fetchall()
    cursor.close()

    return render_template("rooms.html", rooms=rooms)

@app.route("/bookings/<int:id_room>", methods=["GET", "POST"])
def booking(id_room):
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM rooms WHERE id_room = %s",
        (id_room,)
    )

    room = cursor.fetchone()

    if room is None:
        cursor.close()
        return "Kamar tidak ditemukan"

    if request.method == "POST":

        if "id_user" not in session:
            return redirect("/login")

        tanggal_checkin = request.form["tanggal_checkin"]
        tanggal_checkout = request.form["tanggal_checkout"]

        checkin = datetime.strptime(tanggal_checkin, "%Y-%m-%d")
        checkout = datetime.strptime(tanggal_checkout, "%Y-%m-%d")

        jumlah_malam = (checkout - checkin).days

        if jumlah_malam <= 0:
            cursor.close()
            return "Tanggal checkout harus setelah check-in"

        total_harga = jumlah_malam * room["harga_per_malam"]

        cursor.execute("""
            INSERT INTO bookings
            (id_user, id_room, tanggal_checkin, tanggal_checkout, total_harga)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            session["id_user"],
            id_room,
            tanggal_checkin,
            tanggal_checkout,
            total_harga
        ))

        db.commit()
        cursor.close()  
        
        return redirect ("/riwayat")

    cursor.close()
        
    return render_template("booking.html", room=room)

@app.route("/riwayat")
def riwayat():
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            bookings.id_booking,
            users.nama,
            rooms.nomor_kamar,
            rooms.tipe_kamar,
            bookings.tanggal_checkin,
            bookings.tanggal_checkout,
            bookings.total_harga,
            bookings.status
        FROM bookings
        JOIN users ON bookings.id_user = users.id_user
        JOIN rooms ON bookings.id_room = rooms.id_room
        ORDER BY bookings.id_booking DESC
    """)

    bookings = cursor.fetchall()
    cursor.close()

    return render_template("bookings.html", bookings=bookings)

@app.route("/bayar/<int:id_booking>")
def bayar(id_booking):
    cursor = db.cursor()
    cursor.execute("UPDATE bookings SET status = 'lunas' WHERE id_booking = %s", (id_booking,))
    db.commit()
    cursor.close()
    return redirect("/riwayat")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form["username"]
    password = request.form["password"]

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    cursor.close()

    if user is None:
        return "Username atau password salah."
    
    session["id_user"] = user["id_user"]
    session["nama"] = user["nama"]
    return redirect("/hotel")
    
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")


    nama = request.form["nama"]
    username = request.form["username"]
    password = request.form["password"]

    cursor = db.cursor()

    sql =  """insert into users (nama, username, password) values (%s, %s, %s)"""
    cursor.execute(sql, (nama, username, password))
    db.commit()
    cursor.close()

    return jsonify({"message": "registrasi berhasil"})

print(app.url_map)

if __name__ == "__main__":
    app.run(debug=True)