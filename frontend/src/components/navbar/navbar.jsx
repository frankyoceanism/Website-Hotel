import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router';
import { useAuth } from '../../data/authcontext.jsx';
import './navbar.css';

function UserIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7" />
    </svg>
  );
}

function Navbar({ solid = false }) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const menuRef = useRef(null);
  const navigate = useNavigate();
  const { user, loading, openAuth, logout } = useAuth();

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Tutup popup profil saat klik di luar atau tekan Esc
  useEffect(() => {
    if (!menuOpen) return;

    const onClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    };
    const onKey = (e) => {
      if (e.key === 'Escape') setMenuOpen(false);
    };

    document.addEventListener('mousedown', onClickOutside);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onClickOutside);
      document.removeEventListener('keydown', onKey);
    };
  }, [menuOpen]);

  const showSolid = solid || isScrolled;

  const handleLogout = async () => {
    setMenuOpen(false);
    await logout();
    navigate('/');
  };

  return (
    <nav className={`navbar-container ${showSolid ? 'navbar-solid' : 'navbar-transparent'}`}>
      <div className="navbar-brand">AmbaVille</div>
      <div className="nav-actions">
        {showSolid && (
          <>
            <Link to="/">Overview</Link>
            <Link to="/rooms">Accomodations</Link>
            <Link to="/experiences">Experiences</Link>
          </>
        )}

        {loading ? (
          // Menahan tempat selama status login dicek, supaya tidak berkedip
          <button className="btn-text" style={{ visibility: 'hidden' }} tabIndex={-1} aria-hidden="true">
            SIGN IN
          </button>
        ) : user ? (
          <div className="nav-profile" ref={menuRef}>
            <button
              type="button"
              className="nav-avatar"
              onClick={() => setMenuOpen((o) => !o)}
              aria-label="Menu profil"
              aria-expanded={menuOpen}
            >
              <UserIcon />
            </button>

            {menuOpen && (
              <div className="nav-menu" role="menu">
                <div className="nav-menu__user">{user.username}</div>

                {user.role === 'admin' ? (
                  <Link to="/admin" role="menuitem" onClick={() => setMenuOpen(false)}>
                    Admin Dashboard
                  </Link>
                ) : (
                  <Link to="/my-bookings" role="menuitem" onClick={() => setMenuOpen(false)}>
                    Your Bookings
                  </Link>
                )}

                <button type="button" role="menuitem" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            )}
          </div>
        ) : (
          <button className="btn-text" onClick={() => openAuth()}>SIGN IN</button>
        )}
      </div>
    </nav>
  );
}

export default Navbar;