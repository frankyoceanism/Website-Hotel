import { useEffect, useState } from "react";
import { Link } from "react-router";
import "./accomo.css";

// Ganti path gambar sesuai file aktual (taruh di public/images/rooms/ atau import dari src/assets)
const ROOM_LEVELS = [
  { id: "standard", name: "Standard", image: "/images/rooms/standard.jpg" },
  { id: "premium", name: "Premium", image: "/images/rooms/premium.jpg" },
  { id: "executive", name: "Executive", image: "/images/rooms/executive.jpg" },
  { id: "presidential", name: "Presidential", image: "/images/rooms/presidential.jpg" },
];

// Jumlah kartu yang terlihat sekaligus mengikuti lebar layar
function getCount() {
  if (window.matchMedia("(max-width: 600px)").matches) return 1;
  if (window.matchMedia("(max-width: 900px)").matches) return 2;
  return 3;
}

function useVisibleCount() {
  const [count, setCount] = useState(getCount);

  useEffect(() => {
    const onResize = () => setCount(getCount());
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return count;
}

function ChevronRight() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
      <path
        d="M9 5l7 7-7 7"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ChevronLeft() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
      <path
        d="M15 5l-7 7 7 7"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function Accommodations() {
  const visible = useVisibleCount();
  const maxIndex = ROOM_LEVELS.length - visible;
  const [index, setIndex] = useState(0);
  const current = Math.min(index, maxIndex);

  const goNext = () => setIndex(Math.min(current + 1, maxIndex));
  const goPrev = () => setIndex(Math.max(current - 1, 0));

  return (
    <section className="acc">
      <h2 className="acc__title">Accommodations</h2>

      <div className="acc__carousel">
        <div className="acc__viewport">
          <ul
            className="acc__track"
            style={{ "--visible": visible, "--index": current }}
          >
            {ROOM_LEVELS.map((room) => (
              <li className="acc__card" key={room.id}>
                <img className="acc__img" src={room.image} alt={`Kamar ${room.name}`} />
                <div className="acc__overlay" />
                <h3 className="acc__name">{room.name}</h3>
              </li>
            ))}
          </ul>
        </div>

        {current > 0 && (
          <button
            type="button"
            className="acc__nav acc__nav--prev"
            onClick={goPrev}
            aria-label="Lihat kamar sebelumnya"
          >
            <ChevronLeft />
          </button>
        )}
        {current < maxIndex && (
          <button
            type="button"
            className="acc__nav acc__nav--next"
            onClick={goNext}
            aria-label="Lihat kamar berikutnya"
          >
            <ChevronRight />
          </button>
        )}
      </div>

      <div className="acc__progress" aria-hidden="true">
        <span
          className="acc__thumb"
          style={{
            width: `${100 / (maxIndex + 1)}%`,
            transform: `translateX(${current * 100}%)`,
          }}
        />
      </div>

      <Link to="/rooms" className="acc_rooms">
        DISCOVER MORE
      </Link>
    </section>
  );
}