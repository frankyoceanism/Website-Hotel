import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import {
  payBooking,
  cancelBooking,
  payLater,
  formatNum,
  formatCountdown,
} from "../../data/bookingservice.js";

function VirtualAccountStep({ booking, onRestart }) {
  const navigate = useNavigate();
  const [status, setStatus] = useState(booking.status);
  const [left, setLeft] = useState(() => Math.max(0, booking.expiresAt - Date.now()));
  const [busy, setBusy] = useState(false);

  // Satu timer per detik; sisa waktu dihitung dari expiresAt (aman saat refresh)
  useEffect(() => {
    if (status !== "pending") return;
    const t = setInterval(() => setLeft(Math.max(0, booking.expiresAt - Date.now())), 1000);
    return () => clearInterval(t);
  }, [status, booking.expiresAt]);

  const expired = status === "pending" && left <= 0;
  const paid = status === "paid";

  const handleSubmit = async () => {
    setBusy(true);
    await payBooking(booking.ref);
    setStatus("paid");
    setBusy(false);
  };

  const handleCancel = async () => {
    if (!window.confirm("Cancel this booking?")) return;
    await cancelBooking(booking.ref);
    navigate("/");
  };

  const handlePayLater = () => {
    payLater(booking.ref);
    navigate("/"); // TODO: ganti ke halaman "Your Bookings" kalau sudah ada
  };

  const heading = paid ? "Payment received" : expired ? "Booking expired" : "Waiting payment";

  return (
    <section className="bk-pay">
      <div className="bk-card">
        <div className="bk-va__ref">
          <small>Booking ref</small>
          <strong>{booking.ref}</strong>
        </div>

        <div className="bk-va__status">
          <h4 className="bk-sum__sub">{heading}</h4>
          {!paid && !expired && <span className="bk-va__timer">Pay within {formatCountdown(left)}</span>}
        </div>

        <div className={`bk-vabox${expired ? " is-expired" : ""}`}>
          <small>Bank transfer · {booking.bank}</small>
          <p className="bk-va__label">Virtual account number</p>
          <p className="bk-va__number">{booking.vaNumber}</p>
          <div className="bk-sum__row">
            <span>{paid ? "Amount paid" : "Amount due"}</span>
            <span>{formatNum(booking.total)} IDR</span>
          </div>
        </div>

        {paid ? (
          <p className="bk-note">Thank you. Your booking is confirmed.</p>
        ) : expired ? (
          <p className="bk-note">The payment time has run out. Start a new booking to reserve again.</p>
        ) : (
          <p className="bk-note">
            Open your banking app, choose Transfer &gt; Virtual Account, and enter the number above.
            This is a simulation: press Submit to mark the payment as received.
          </p>
        )}

        <div className="bk-actions">
          {paid && (
            <button type="button" className="bk-btn bk-btn--wide" onClick={() => navigate("/")}>
              Back to overview
            </button>
          )}
          {expired && (
            <>
              <button type="button" className="bk-btn" onClick={onRestart}>New booking</button>
              <button type="button" className="bk-btn bk-btn--tan" onClick={() => navigate("/")}>Back to overview</button>
            </>
          )}
          {!paid && !expired && (
            <>
              <button type="button" className="bk-btn" disabled={busy} onClick={handleSubmit}>Submit</button>
              <button type="button" className="bk-btn bk-btn--danger" onClick={handleCancel}>Cancel</button>
              <button type="button" className="bk-btn bk-btn--tan bk-btn--wide" onClick={handlePayLater}>Pay later</button>
            </>
          )}
        </div>
      </div>
    </section>
  );
}

export default VirtualAccountStep;