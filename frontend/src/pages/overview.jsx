import Navbar from '../components/navbar/navbar.jsx';
import Hero from '../components/hero/hero.jsx';
import About from '../components/about/about.jsx';
import Accommodations from '../components/accomodations/accomo.jsx';
import Experiences from '../components/experience/experience.jsx';

function Overview() {
  return (
    <>
      <Navbar/> 
      <Hero />
      <About />
      <Accommodations />
      <Experiences />
    </>
  );
}

export default Overview;