const STEPS = ["Dates", "Accommodation", "Experiences", "Payment", "Confirmation"];

function BookingStepper({ step, onGo }) {
  return (
    <nav className="bk-stepper" aria-label="Booking progress">
      {STEPS.map((label, i) => {
        const n = i + 1;
        const state = n === step ? "is-active" : n < step ? "is-done" : "";
        return (
          <button
            key={label}
            type="button"
            className={`bk-stepper__item ${state}`}
            disabled={!(n < step && step < 5)}
            onClick={() => onGo(n)}
            aria-current={n === step ? "step" : undefined}
          >
            <span className="bk-stepper__num">{n}</span>
            <span className="bk-stepper__label">{label}</span>
          </button>
        );
      })}
    </nav>
  );
}

export default BookingStepper;