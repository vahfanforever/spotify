import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const SpotifyAuth = () => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    const handleLogin = async () => {
        try {
            setError(null);
            console.log('Fetching Spotify auth URL...');

            const response = await fetch('http://localhost:5000/api/login', {
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Received auth URL:', data.auth_url);

            if (data.auth_url) {
                // Directly navigate to Spotify
                window.open(data.auth_url, '_self');
            } else {
                throw new Error('No auth URL received');
            }
        } catch (error) {
            console.error('Login error:', error);
            setError(`Failed to initiate Spotify login: ${error.message}`);
        }
    };

    // ... rest of your component code ...

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="card-header">
                    <h2>Spotify Integration</h2>
                </div>
                <div className="card-content">
                    {error && (
                        <div className="error-message">
                            {error}
                        </div>
                    )}

                    <button
                        onClick={handleLogin}
                        className="login-button"
                    >
                        Connect to Spotify
                    </button>
                </div>
            </div>

            <style>{`
        .auth-container {
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 100vh;
          background-color: #f5f5f5;
          padding: 20px;
        }

        .auth-card {
          background: white;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          width: 100%;
          max-width: 400px;
          padding: 20px;
        }

        .card-header {
          margin-bottom: 20px;
        }

        .card-header h2 {
          margin: 0;
          color: #333;
          font-size: 24px;
        }

        .card-content {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .error-message {
          color: #dc2626;
          background-color: #fee2e2;
          padding: 8px 12px;
          border-radius: 4px;
          text-align: center;
        }

        .login-button {
          background-color: #1DB954;
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 4px;
          font-size: 16px;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .login-button:hover {
          background-color: #1ed760;
        }
      `}</style>
        </div>
    );
};

export default SpotifyAuth;