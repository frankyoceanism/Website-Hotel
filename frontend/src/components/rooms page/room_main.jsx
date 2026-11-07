import { useState } from "react";
import { useNavigate } from "react-router";
import rooms from "../../data/rooms";
import RoomDetailsModal from "../rooms page/room_detail";
import "./room_main.css";

function RoomShowcase() {
  const [selectedRoom, setSelectedRoom] = useState(null);
  const navigate = useNavigate();

  const handleBooking = (room) => {
    navigate(`/bookings?room=${encodeURIComponent(room.name)}`);
  };

  const handleReserve = () => {
    navigate("/bookings");
  };

  return (
    <main className="rooms-page">

      {/* ACCOMMODATION HEADER */}
      <section className="rooms-intro">
        <h1>Accommodation at AmbaFlat</h1>
        <p>
          Inspired by the ancient Bodhisat anecdote of Borehuka,
          AmbaPuri Pavilions and Ulla Kame offer a distinctive
          accommodation experience surrounded by comfort,
          tranquility, and thoughtful hospitality.
        </p>
      </section>


      {/* ALL STAYS INCLUDE */}
      <section className="all-stays">
        <h2>All stays include</h2>
        <div className="amenities-grid">
          <div className="amenity-item">
            Welcome Refreshment
          </div>
          <div className="amenity-item">
            Daily Breakfast
          </div>
          <div className="amenity-item">
            Swimming Pool Access
          </div>
          <div className="amenity-item">
            Premium Bathroom Amenities
          </div>
        </div>
        <button
          className="reserve-button"
          onClick={handleReserve}>
          Reserve
        </button>
      </section>


      {/* ROOM CATEGORIES */}
      <section className="room-categories">
        <div className="room-grid">
          {rooms.map((room) => (
            <article className="room-card" key={room.id}>
              <div className="room-card-image">
                <img
                  src={room.images[0]}
                  alt={`${room.name} accommodation`}
                  loading="lazy"/>
              </div>
              <div className="room-card-content">
                <span className="room-category">
                  {room.category}
                </span>
                <h3>{room.name}</h3>
                <p>{room.description}</p>
                <button
                  className="room-details-button"
                  onClick={() => setSelectedRoom(room)}>
                  Lihat Selengkapnya
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>


      {/* EXPERIENCES OFFERS */}
      <section className="experience-offer">

        <h2>Experiences offers</h2>

        <p>
          Discover our experiences offers at AmbaFlat.
        </p>

        <button
          onClick={() => navigate("/experiences")}
        >
          Discover it
        </button>

      </section>


      {/* ROOM DETAILS MODAL */}
      {selectedRoom && (
        <RoomDetailsModal
          room={selectedRoom}
          onClose={() => setSelectedRoom(null)}
          onBook={() => handleBooking(selectedRoom)}
        />
      )}

    </main>
  );
}

export default RoomShowcase;