import { Routes, Route } from 'react-router'
import Overview from './pages/overview.jsx';
import Rooms from './pages/rooms.jsx';
import Experience from './pages/experiencesPage.jsx';


function App() {

  return (
   <Routes>
      <Route path="/" element={<Overview />} />
      <Route path="/rooms" element={<Rooms/>} />
      <Route path="/experiences" element={<Experience />} />
    </Routes>
  );
}

export default App;