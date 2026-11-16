import { useState } from "react";
import { Link } from "react-router";
import { formatNum, roomLabel } from "../../data/bookingservice.js";

function RoomImages({ images = [], alt }) {
  const [i, setI] = useState(0);
  const many = images.length > 1;
  const go = (n) => setI((i + n + images.length) % images.length);

  return (
    <div className="bk-room__media">
      {images.length > 0 && <img src={images[i]} alt={alt} />}
      {many && (
        <>
          <button type="button" className="bk-room__arrow bk-room__arrow--prev" onClick={() => go(-1)} aria-label="Previous photo">‹</button>
          <button type="button" className="bk-room__arrow bk-room__arrow--next" onClick={() => go(1)} aria-label="Next photo">›</button>
          <div className="bk-room__dots">
            {images.map((_, n) => (
              <span key={n} className={`bk-dot${n === i ? " is-on" : ""}`} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function RoomStep({ rooms, guests, selectedId, onSelect }) {
  return (
    <section>
      <h2 className="bk-title">Select your accommodations</h2>
      <div className="bk-rooms">
        {rooms.map((room) => {
          const fits = room.capacity >= guests;
          return (
            <article key={room.id} className={`bk-room${fits ? "" : " is-disabled"}`}>
              <RoomImages images={room.images} alt={roomLabel(room)} />
              <div className="bk-room__info">
                <div className="bk-room__top">
                  <h3>{roomLabel(room)}</h3>
                  <button
                    className="bk-room__link"
                    onClick={() => setSelectedRoom(room)}>
                      Room Details
                  </button>
                </div>
                <p className="bk-room__desc">{room.description}</p>
                <p className="bk-room__meta">
                  {room.size} · {room.bedType} · Up to {room.capacity} guests
                </p>
                <div className="bk-room__bottom">
                  <div className="bk-room__price">
                    <small>Rates from</small>
                    <strong>{formatNum(room.price)}</strong> IDR / Night
                  </div>
                  <button
                    type="button"
                    className="bk-pill"
                    disabled={!fits}
                    onClick={() => onSelect(room.id)}
                  >
                    {!fits ? `Max ${room.capacity} guests` : selectedId === room.id ? "Selected" : "Select"}
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export default RoomStep;