// =====================================================================
// bookingService.js
// Satu-satunya file yang perlu diganti saat backend Flask siap.
// Sekarang semua fungsi memakai data dari /data dan data palsu.
// Komponen tidak tahu data datang dari mana, jadi tidak perlu diubah.
// =====================================================================
import rooms from "../data/rooms.js";
import experiences from "../data/experience.js";

const HOLD_MS = 2 * 60 * 60 * 1000; // batas waktu bayar: 2 jam
const STORAGE_KEY = "luxe_current_booking";
const wait = (ms = 200) => new Promise((resolve) => setTimeout(resolve, ms));

/* ---------- Helper tampilan & tanggal (tetap dipakai setelah Flask) ---------- */

export const formatNum = (n) => Math.round(n).toLocaleString("en-US");

export const roomLabel = (room) =>
  `${room.name} ${room.category === "SUITE" ? "Suite" : "Rooms"}`;

// Tanggal disimpan sebagai teks "YYYY-MM-DD" (mudah dikirim ke Flask/MySQL)
export const toISO = (date) => {
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${m}-${d}`;
};

export const parseISO = (iso) => {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
};

export const nightsBetween = (checkIn, checkOut) =>
  Math.round((parseISO(checkOut) - parseISO(checkIn)) / 86400000);

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export const formatDateParts = (iso) => {
  const d = parseISO(iso);
  return {
    day: String(d.getDate()),
    label: `${WEEKDAYS[d.getDay()]}, ${MONTHS[d.getMonth()]}, ${d.getFullYear()}`,
  };
};

export const formatCountdown = (ms) => {
  const s = Math.floor(ms / 1000);
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(Math.floor(s / 3600))}:${pad(Math.floor((s % 3600) / 60))}:${pad(s % 60)}`;
};

/* ---------- Fungsi data (nanti diganti fetch ke Flask) ---------- */

// Dipakai tombol Reserve di halaman accommodation.
// FLASK: cek token/session login ke backend.
export const isLoggedIn = () => true;

// FLASK: GET /api/experiences
export async function getExperiences() {
  await wait();
  return experiences;
}

// FLASK: GET /api/rooms/availability?check_in=&check_out=&guests=
// Sekarang semua kamar dianggap tersedia.
export async function searchAvailability({ checkIn, checkOut, guests }) {
  await wait();
  return rooms.map((room) => ({ ...room, available: true }));
}

// FLASK: POST /api/bookings
// Di backend, Python membuat ref, nomor VA acak, dan expiresAt, lalu
// menghitung ulang total dari database (jangan percaya total dari frontend).
export async function createBooking(payload) {
  await wait(400);
  const booking = {
    ...payload,
    ref: `BK${Math.floor(1000 + Math.random() * 9000)}`,
    vaNumber: makeVirtualAccount(),
    status: "pending",
    expiresAt: Date.now() + HOLD_MS,
  };
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(booking));
  return booking;
}

// FLASK: PATCH /api/bookings/<ref>/pay  (simulasi "sudah transfer")
export async function payBooking(ref) {
  await wait();
  clearCurrentBooking();
  return { ref, status: "paid" };
}

// FLASK: PATCH /api/bookings/<ref>/cancel
export async function cancelBooking(ref) {
  await wait();
  clearCurrentBooking();
  return { ref, status: "cancelled" };
}

// Pay Later: di backend booking tetap "pending" di database.
// Di frontend cukup dilepas dari sessionStorage.
export function payLater() {
  clearCurrentBooking();
}

/* ---------- Penyimpanan sementara (agar refresh di langkah 5 aman) ---------- */

export function getCurrentBooking() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY));
    return saved && saved.status === "pending" ? saved : null;
  } catch {
    return null;
  }
}

export function clearCurrentBooking() {
  sessionStorage.removeItem(STORAGE_KEY);
}

function makeVirtualAccount() {
  let digits = "8077";
  for (let i = 0; i < 12; i++) digits += Math.floor(Math.random() * 10);
  return digits.match(/.{4}/g).join(" ");
}
