import { useState } from "react";
import { formatDateParts, formatNum, roomLabel } from "../../data/bookingservice.js";

// sticky = true  -> panel kanan yang menempel saat scroll (langkah 3).
//                  Di mobile jadi bar di bawah, dibuka dengan ditekan.
// sticky = false -> rekap biasa di dalam kartu (langkah 4).
function BookingSummary({ summary, sticky = false, children }) {
  const [open, setOpen] = useState(false);
  const { checkIn, checkOut, guests, room, addons, nights, roomTotal, addonTotal, total } = summary;
  const ci = formatDateParts(checkIn);
  const co = formatDateParts(checkOut);

  return (
    <aside className={`bk-summary${sticky ? " bk-summary--sticky" : ""}${open ? " is-open" : ""}`}>
      {sticky && (
        <button type="button" className="bk-summary__toggle" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
          <span>Total</span>
          <strong>{formatNum(total)} IDR</strong>
          <span aria-hidden="true">{open ? "▾" : "▴"}</span>
        </button>
      )}

      <div className="bk-summary__body">
        <div className="bk-sum__dates">
          <div>
            <small>Check in</small>
            <b>{ci.day}</b>
            <span>{ci.label}</span>
          </div>
          <div>
            <small>Check out</small>
            <b>{co.day}</b>
            <span>{co.label}</span>
          </div>
        </div>

        <div className="bk-sum__room">
          <h4>{room ? roomLabel(room) : ""}</h4>
          <p>{guests} Guest</p>
          {addons.length > 0 && (
            <>
              <h4 className="bk-sum__sub">Experiences:</h4>
              <ul>
                {addons.map((a) => (
                  <li key={a.id}>{a.title}</li>
                ))}
              </ul>
            </>
          )}
        </div>

        <h4 className="bk-sum__sub">Your stay</h4>
        <div className="bk-sum__row">
          <span>Rooms · {nights} {nights === 1 ? "night" : "nights"}</span>
          <span>{formatNum(roomTotal)} IDR</span>
        </div>
        {addons.length > 0 && (
          <div className="bk-sum__row">
            <span>Experiences</span>
            <span>{formatNum(addonTotal)} IDR</span>
          </div>
        )}
        <div className="bk-sum__row bk-sum__total">
          <span>Total</span>
          <span>{formatNum(total)} IDR</span>
        </div>
      </div>

      {children}
    </aside>
  );
}

export default BookingSummary;