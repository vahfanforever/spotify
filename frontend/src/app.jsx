import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const App = () => {
    const [authStatus, setAuthStatus] = useState({
        authenticated: false,
        tokenInfo: null
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        checkAuthStatus();
    }, []);

    const checkAuthStatus = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/auth/status', {
                credentials: 'include'  // Important for sending cookies
            });
            const data = await response.json();
            setAuthStatus(data);
        } catch (error) {
            console.error('Error checking auth status:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleLogin = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/login', {
                credentials: 'include'
            });
            const data = await response.json();
            // Redirect to Spotify authorization
            window.location.href = data.auth_url;
        } catch (error) {
            console.error('Error initiating login:', error);
        }
    };

    const handleLogout = async () => {
        try {
            await fetch('http://localhost:5000/api/logout', {
                credentials: 'include'
            });
            setAuthStatus({ authenticated: false, tokenInfo: null });
        } catch (error) {
            console.error('Error logging out:', error);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-lg">Loading...</div>
            </div>
        );
    }

    return (
        <div className="container mx-auto p-4 max-w-md">
            <Card>
                <CardHeader>
                    <CardTitle>Spotify Queue Manager</CardTitle>
                </CardHeader>
                <CardContent>
                    {!authStatus.authenticated ? (
                        <div className="space-y-4">
                            <p className="text-center">Welcome! Please login to continue.</p>
                            <Button
                                className="w-full"
                                onClick={handleLogin}
                            >
                                Login with Spotify
                            </Button>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <div className="p-4 bg-gray-50 rounded-lg">
                                <h3 className="font-medium mb-2">Authentication Status</h3>
                                <p className="text-sm text-gray-600">
                                    Token expires at: {' '}
                                    {new Date(authStatus.token_info.expires_at * 1000).toLocaleString()}
                                </p>
                            </div>

                            <div className="flex justify-between items-center">
                                <Button
                                    variant="outline"
                                    onClick={handleLogout}
                                >
                                    Logout
                                </Button>
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
};

export default App;