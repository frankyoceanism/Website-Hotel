import { useEffect } from "react";
import { useNavigate } from "react-router";
import { useAuth } from "../data/authcontext.jsx";
import Navbar from "../components/navbar/navbar.jsx";
import Booking from "../components/booking/booking_alur.jsx";

function Bookings() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (loading) return;

    if (!user) {
      navigate("/", { replace: true });
    } else if (user.role === "admin") {
      navigate("/admin", { replace: true });
    }
  }, [user, loading, navigate]);

  // Jangan tampilkan form booking sebelum status login jelas
  if (loading || !user || user.role === "admin") return null;

  return (
    <>
      <Navbar solid />
      <Booking />
    </>
  );
}

export default Bookings;