import { useEffect, useState } from "react";
import "./room_detail.css";

function RoomDetailsModal({ room, onClose, }) {
  const [activeImage, setActiveImage] = useState(0);
  const images = room.images;
  const nextImage = () => {
    setActiveImage((current) =>
      (current + 1) % images.length
    );
  };
  const previousImage = () => {
    setActiveImage((current) =>
      (current - 1 + images.length) % images.length
    );
  };
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("keydown", handleEscape);
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  const formatPrice = (price) => {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      maximumFractionDigits: 0,
    }).format(price);
  };

  return (
    <div
      className="room-modal-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >

      <div
        className="room-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="room-modal-title"
      >

        <button
          className="room-modal-close"
          onClick={onClose}
          aria-label="Close modal"
        >
          ×
        </button>


        {/* GALLERY */}

        <div className="room-modal-gallery">

          <img
            src={images[activeImage]}
            alt={`${room.name} view ${activeImage + 1}`}
          />

          {images.length > 1 && (
            <>
              <button
                className="gallery-arrow gallery-prev"
                onClick={previousImage}
                aria-label="Previous image"
              >
                &#10094;
              </button>

              <button
                className="gallery-arrow gallery-next"
                onClick={nextImage}
                aria-label="Next image"
              >
                &#10095;
              </button>

              <div className="gallery-counter">
                {activeImage + 1} / {images.length}
              </div>
            </>
          )}

        </div>


        {/* ROOM INFORMATION */}

        <div className="room-modal-content">

          <span className="room-category">
            {room.category}
          </span>

          <h2 id="room-modal-title">{room.name}</h2>

          <p className="room-modal-description">
            {room.description}
          </p>


          <div className="room-specifications">

            <div>
              <span>Room Size</span>
              <strong>{room.size}</strong>
            </div>

            <div>
              <span>Maximum Guests</span>
              <strong>{room.capacity} Guests</strong>
            </div>

            <div>
              <span>Bed Type</span>
              <strong>{room.bedType}</strong>
            </div>

          </div>


          <div className="room-modal-amenities">

            <h3>Room Amenities</h3>

            <ul>
              {room.amenities.map((amenity, index) => (
                <li key={index}>{amenity}</li>
              ))}
            </ul>

          </div>


          <div className="room-modal-footer">

            <div className="room-modal-price">
              <span>Starting from</span>
              <strong>{formatPrice(room.price)}</strong>
              <small>/ night</small>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}

export default RoomDetailsModal;
