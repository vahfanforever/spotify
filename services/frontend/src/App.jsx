// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import SpotifyAuth from './components/SpotifyAuth';
import SpotifyDashboard from './components/SpotifyDashboard';

// Get API URL from environment variable
const API_URL = import.meta.env.VITE_API_URL;

// Protected Route component to handle authentication
const ProtectedRoute = ({ children }) => {
  // Check if user is authenticated
  const checkAuth = async () => {
    try {
      const response = await fetch(`${API_URL}/v1/auth/status`, {
        credentials: 'include'
      });
      const data = await response.json();
      return data.authenticated;
    } catch (error) {
      console.error('Auth check failed:', error);
      console.error('API URL being used:', API_URL); // Debug log
      return false;
    }
  };

  const [isAuthenticated, setIsAuthenticated] = React.useState(null);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    console.log('Current API URL:', API_URL); // Debug log
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
  // Log API URL when app starts
  React.useEffect(() => {
    console.log('App initialized with API URL:', API_URL);
  }, []);

  return (
    <Router basename="/spotify-connector">
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