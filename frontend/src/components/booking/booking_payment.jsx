import BookingSummary from "./booking_sum.jsx";

// Logo sementara berupa teks. Ganti dengan <img> kalau file logo sudah ada.
const BANKS = [
  { id: "BCA", label: "BCA" },
  { id: "MANDIRI", label: "mandiri" },
  { id: "BNI", label: "BNI" },
];

function PaymentStep({ summary, busy, onBank, onConfirm }) {
  return (
    <section className="bk-pay">
      <div className="bk-card">
        <BookingSummary summary={summary} />

        <h4 className="bk-sum__sub bk-pay__heading">Payment</h4>
        <div className="bk-banks">
          {BANKS.map((b) => (
            <button
              key={b.id}
              type="button"
              className={`bk-bank bk-bank--${b.id.toLowerCase()}${summary.bank === b.id ? " is-on" : ""}`}
              onClick={() => onBank(b.id)}
              aria-pressed={summary.bank === b.id}
            >
              <span className="bk-bank__dot" />
              {b.label}
            </button>
          ))}
        </div>
        <p className="bk-note">A virtual account number will be shown after you confirm.</p>

        <button type="button" className="bk-btn" disabled={busy} onClick={onConfirm}>
          {busy ? "Processing…" : "Confirm"}
        </button>
      </div>
    </section>
  );
}

export default PaymentStep;