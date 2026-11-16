import { Routes, Route } from 'react-router'
import Overview from './pages/overview.jsx';
import Rooms from './pages/rooms.jsx';
import Experience from './pages/experiencesPage.jsx';
import Bookings from './pages/bookings.jsx';


function App() {

  return (
   <Routes>
      <Route path="/" element={<Overview />} />
      <Route path="/rooms" element={<Rooms/>} />
      <Route path="/experiences" element={<Experience />} />
      <Route path="/bookings" element={<Bookings/>}/>
    </Routes>
  );
}

export default App;