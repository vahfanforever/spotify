import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SpotifyAuth from './components/SpotifyAuth';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<SpotifyAuth />} />
        <Route path="/dashboard" element={<SpotifyAuth />} />
      </Routes>
    </Router>
  );
}

export default App;