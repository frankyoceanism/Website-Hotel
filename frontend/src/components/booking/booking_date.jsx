import { useState } from "react";
import { toISO, formatDateParts } from "../../data/bookingservice.js";

const DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

// Isi kalender satu bulan: sel kosong di awal, lalu tanggal "YYYY-MM-DD"
function buildMonth(year, month) {
  const lead = new Date(year, month, 1).getDay();
  const count = new Date(year, month + 1, 0).getDate();
  return [
    ...Array(lead).fill(null),
    ...Array.from({ length: count }, (_, i) => toISO(new Date(year, month, i + 1))),
  ];
}

function DateStep({ checkIn, checkOut, guests, busy, onChange, onSearch }) {
  const today = new Date();
  const todayISO = toISO(today);
  const thisMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  const [view, setView] = useState(thisMonth);

  const shift = (n) => setView((v) => new Date(v.getFullYear(), v.getMonth() + n, 1));
  const atStart = view.getTime() <= thisMonth.getTime();

  // Klik 1 = check-in, klik 2 (setelah check-in) = check-out
  const pick = (iso) => {
  if (!checkIn) onChange({ checkIn: iso, checkOut: null });          
  else if (iso === checkIn) onChange({ checkIn: null, checkOut: null }); 
  else if (iso < checkIn) onChange({ checkIn: iso, checkOut: null });   
  else onChange({ checkOut: iso });                                      
};

  const dayClass = (iso) => {
    const c = ["bk-day"];
    if (iso === checkIn) c.push("is-range", "is-start", !checkOut ? "is-solo" : "");
    else if (iso === checkOut) c.push("is-range", "is-end");
    else if (checkIn && checkOut && iso > checkIn && iso < checkOut) c.push("is-range");
    return c.join(" ");
  };

  const renderMonth = (date) => (
    <div className="bk-cal__month">
      <h3 className="bk-cal__title">
        {MONTHS[date.getMonth()]} {date.getFullYear()}
      </h3>
      <div className="bk-cal__grid">
        {DOW.map((d) => (
          <span key={d} className="bk-cal__dow">{d}</span>
        ))}
        {buildMonth(date.getFullYear(), date.getMonth()).map((iso, i) =>
          iso ? (
            <button
              key={iso}
              type="button"
              className={dayClass(iso)}
              disabled={iso < todayISO}
              onClick={() => pick(iso)}
            >
              {Number(iso.slice(8))}
            </button>
          ) : (
            <span key={`blank-${i}`} />
          )
        )}
      </div>
    </div>
  );

  const nextView = new Date(view.getFullYear(), view.getMonth() + 1, 1);
  const ci = checkIn ? formatDateParts(checkIn) : null;
  const co = checkOut ? formatDateParts(checkOut) : null;

  return (
    <section className="bk-dates">
      <div className="bk-cal">
        <div className="bk-cal__head">Select your dates</div>
        <div className="bk-cal__body">
          <button type="button" className="bk-cal__nav bk-cal__nav--prev" disabled={atStart} onClick={() => shift(-1)} aria-label="Previous month">←</button>
          {renderMonth(view)}
          {renderMonth(nextView)}
          <button type="button" className="bk-cal__nav bk-cal__nav--next" onClick={() => shift(1)} aria-label="Next month">→</button>
        </div>
      </div>

      <div className="bk-panel">
        <div className="bk-ci">
          <div className="bk-ci__col">
            <div className="bk-ci__label">Check-in</div>
            <div className="bk-ci__day">{ci ? ci.day : "–"}</div>
            <div className="bk-ci__date">{ci ? ci.label : "Select a date"}</div>
          </div>
          <div className="bk-ci__col">
            <div className="bk-ci__label">Check-out</div>
            <div className="bk-ci__day">{co ? co.day : "–"}</div>
            <div className="bk-ci__date">{co ? co.label : "Select a date"}</div>
          </div>
        </div>

        <select
          className="bk-select"
          value={guests}
          onChange={(e) => onChange({ guests: Number(e.target.value) })}
          aria-label="Number of guests"
        >
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <option key={n} value={n}>{n} Guest</option>
          ))}
        </select>

        <button
          type="button"
          className="bk-btn bk-btn--outline"
          disabled={!checkIn || !checkOut || busy}
          onClick={onSearch}
        >
          {busy ? "Searching…" : "Search availability"}
        </button>
      </div>
    </section>
  );
}

export default DateStep;