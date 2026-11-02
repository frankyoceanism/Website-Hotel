import { useState, useEffect } from 'react';
import { Link } from 'react-router';
import Auth from '../authentification/auth.jsx';
import './navbar.css';

function Navbar({ solid = false }) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const showSolid = solid || isScrolled;
  

  return (
    <>
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
        <button className="btn-text" onClick={() => setAuthOpen(true)}>SIGN IN</button>
      </div>
    </nav>

    <Auth open={authOpen} onClose={() => setAuthOpen(false)} />
    </>
  );
}

export default Navbar;