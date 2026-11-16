import BookingSummary from "./booking_sum.jsx";
import { formatNum } from "../../data/bookingservice.js";

function AddonStep({ experiences, addonIds, summary, onToggle, onNext }) {
  return (
    <section className="bk-addons">
      <div className="bk-addon-list">
        {experiences.map((exp) => {
          const added = addonIds.includes(exp.id);
          return (
            <article key={exp.id} className="bk-addon">
              <img src={exp.image} alt={exp.title} />
              <div className="bk-addon__text">
                <h3>{exp.title}</h3>
                <p>{exp.description}</p>
                <div className="bk-addon__foot">
                  <span>{formatNum(exp.price)} IDR</span>
                  <button
                    type="button"
                    className={`bk-add${added ? " is-added" : ""}`}
                    onClick={() => onToggle(exp.id)}
                    aria-pressed={added}
                  >
                    {added ? "Added ✓" : "+ Add"}
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </div>

      <BookingSummary summary={summary} sticky>
        <button type="button" className="bk-btn" onClick={onNext}>Next step →</button>
      </BookingSummary>
    </section>
  );
}

export default AddonStep;