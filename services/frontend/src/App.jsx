// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import SpotifyAuth from './components/SpotifyAuth';
import SpotifyDashboard from './components/SpotifyDashboard';

// Protected Route component to handle authentication
const ProtectedRoute = ({ children }) => {
  // Check if user is authenticated
  const checkAuth = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/auth/status', {
        credentials: 'include'
      });
      const data = await response.json();
      return data.authenticated;
    } catch (error) {
      console.error('Auth check failed:', error);
      return false;
    }
  };

  const [isAuthenticated, setIsAuthenticated] = React.useState(null);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    checkAuth().then(authenticated => {
      setIsAuthenticated(authenticated);
      setIsLoading(false);
    });
  }, []);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return isAuthenticated ? children : <Navigate to="/" />;
};

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<SpotifyAuth />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <SpotifyDashboard />
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
};

export default App;