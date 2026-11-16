import { useEffect, useState } from "react";
import BookingStepper from "./booking_stepper.jsx";
import DateStep from "./booking_date.jsx";
import RoomStep from "./booking_rooms.jsx";
import AddonStep from "./booking_addon.jsx";
import PaymentStep from "./booking_payment.jsx";
import VirtualAccountStep from "./booking_va.jsx";
import {
  searchAvailability,
  getExperiences,
  createBooking,
  getCurrentBooking,
  clearCurrentBooking,
  nightsBetween,
} from "../../data/bookingservice.js";
import "./booking.css";

const INITIAL = {
  checkIn: null, // "YYYY-MM-DD"
  checkOut: null,
  guests: 2,
  roomId: null,
  addonIds: [],
  bank: "BCA",
};

// Langkah: 1 tanggal, 2 kamar, 3 add-on, 4 pembayaran, 5 virtual account
function Booking() {
  const [step, setStep] = useState(1);
  const [data, setData] = useState(INITIAL);
  const [rooms, setRooms] = useState([]);
  const [experiences, setExperiences] = useState([]);
  const [booking, setBooking] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getExperiences().then(setExperiences);
    const saved = getCurrentBooking(); // refresh di langkah 5 tidak kehilangan booking
    if (saved) {
      setBooking(saved);
      setStep(5);
    }
  }, []);

  const update = (patch) => setData((d) => ({ ...d, ...patch }));

  // Ringkasan dihitung di sini, dipakai langkah 3 dan 4
  const nights = data.checkIn && data.checkOut ? nightsBetween(data.checkIn, data.checkOut) : 0;
  const room = rooms.find((r) => r.id === data.roomId) || null;
  const addons = experiences.filter((e) => data.addonIds.includes(e.id));
  const roomTotal = room ? room.price * nights : 0;
  const addonTotal = addons.reduce((sum, a) => sum + a.price, 0);
  const summary = {
    ...data,
    room,
    addons,
    nights,
    roomTotal,
    addonTotal,
    total: roomTotal + addonTotal,
  };

  const handleSearch = async () => {
    setBusy(true);
    const list = await searchAvailability(data);
    setRooms(list);
    update({ roomId: null });
    setBusy(false);
    setStep(2);
  };

  const handleSelectRoom = (id) => {
    update({ roomId: id });
    setStep(3);
  };

  const toggleAddon = (id) =>
    update({
      addonIds: data.addonIds.includes(id)
        ? data.addonIds.filter((x) => x !== id)
        : [...data.addonIds, id],
    });

  const handleConfirm = async () => {
    setBusy(true);
    const created = await createBooking({
      checkIn: data.checkIn,
      checkOut: data.checkOut,
      guests: data.guests,
      roomId: data.roomId,
      addonIds: data.addonIds,
      bank: data.bank,
      total: summary.total,
    });
    setBooking(created);
    setBusy(false);
    setStep(5);
  };

  const restart = () => {
    clearCurrentBooking();
    setBooking(null);
    setData(INITIAL);
    setStep(1);
  };

  const goTo = (n) => {
    if (step < 5 && n < step) setStep(n);
  };

  return (
    <main className="bk">
      <div className="bk-inner">
        <BookingStepper step={step} onGo={goTo} />

        {step > 1 && step < 5 && (
          <button type="button" className="bk-back" onClick={() => setStep(step - 1)}>
            ← Back
          </button>
        )}

        {step === 1 && (
          <DateStep
            checkIn={data.checkIn}
            checkOut={data.checkOut}
            guests={data.guests}
            busy={busy}
            onChange={update}
            onSearch={handleSearch}
          />
        )}

        {step === 2 && (
          <RoomStep
            rooms={rooms}
            guests={data.guests}
            selectedId={data.roomId}
            onSelect={handleSelectRoom}
          />
        )}

        {step === 3 && (
          <AddonStep
            experiences={experiences}
            addonIds={data.addonIds}
            summary={summary}
            onToggle={toggleAddon}
            onNext={() => setStep(4)}
          />
        )}

        {step === 4 && (
          <PaymentStep
            summary={summary}
            busy={busy}
            onBank={(bank) => update({ bank })}
            onConfirm={handleConfirm}
          />
        )}

        {step === 5 && booking && <VirtualAccountStep booking={booking} onRestart={restart} />}
      </div>
    </main>
  );
}

export default Booking;