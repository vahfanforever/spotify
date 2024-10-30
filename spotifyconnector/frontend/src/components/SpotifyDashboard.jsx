import React, { useState, useEffect } from 'react';
import { Search, Plus, Trash2, Link } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

const SpotifyDashboard = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [selectedSongs, setSelectedSongs] = useState([]);
    const [isSearching, setIsSearching] = useState(false);
    const [error, setError] = useState(null);

    // Function to search songs using Spotify API
    const searchSongs = async () => {
        if (!searchQuery.trim()) return;

        setIsSearching(true);
        setError(null);

        try {
            // First check if we're still authenticated
            const authResponse = await fetch('http://localhost:5000/api/auth/status', {
                credentials: 'include'
            });
            const authData = await authResponse.json();

            if (!authData.authenticated) {
                throw new Error('Authentication expired');
            }

            // Use the access token to search Spotify
            const response = await fetch(`https://api.spotify.com/v1/search?q=${encodeURIComponent(searchQuery)}&type=track&limit=10`, {
                headers: {
                    'Authorization': `Bearer ${authData.token_info.access_token}`
                }
            });

            if (!response.ok) throw new Error('Failed to search songs');

            const data = await response.json();
            setSearchResults(data.tracks.items);
        } catch (err) {
            setError(err.message);
            console.error('Search error:', err);
        } finally {
            setIsSearching(false);
        }
    };

    // Add song to selected list
    const addSong = (song) => {
        if (!selectedSongs.find(s => s.id === song.id)) {
            setSelectedSongs([...selectedSongs, song]);
        }
    };

    // Remove song from selected list
    const removeSong = (songId) => {
        setSelectedSongs(selectedSongs.filter(song => song.id !== songId));
    };

    return (
        <div className="p-6 max-w-6xl mx-auto">
            <Card className="mb-6">
                <CardHeader>
                    <CardTitle>Link Your Songs</CardTitle>
                </CardHeader>
                <CardContent>
                    {/* Search Section */}
                    <div className="flex gap-4 mb-6">
                        <div className="relative flex-1">
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && searchSongs()}
                                placeholder="Search for songs..."
                                className="w-full p-2 pl-10 border rounded-md"
                            />
                            <Search className="absolute left-3 top-2.5 text-gray-400" size={20} />
                        </div>
                        <button
                            onClick={searchSongs}
                            disabled={isSearching}
                            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-green-300"
                        >
                            {isSearching ? 'Searching...' : 'Search'}
                        </button>
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="p-4 mb-4 text-red-700 bg-red-100 rounded-md">
                            {error}
                        </div>
                    )}

                    {/* Search Results */}
                    <div className="mb-8">
                        <h3 className="text-lg font-semibold mb-4">Search Results</h3>
                        <div className="space-y-2">
                            {searchResults.map(song => (
                                <div key={song.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                                    <div className="flex items-center gap-4">
                                        {song.album.images[2] && (
                                            <img
                                                src={song.album.images[2].url}
                                                alt={song.album.name}
                                                className="w-10 h-10 rounded"
                                            />
                                        )}
                                        <div>
                                            <div className="font-medium">{song.name}</div>
                                            <div className="text-sm text-gray-600">
                                                {song.artists.map(artist => artist.name).join(', ')}
                                            </div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => addSong(song)}
                                        className="p-2 text-green-600 hover:bg-green-50 rounded-full"
                                    >
                                        <Plus size={20} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Selected Songs */}
                    <div>
                        <h3 className="text-lg font-semibold mb-4">Selected Songs</h3>
                        <div className="space-y-2">
                            {selectedSongs.map(song => (
                                <div key={song.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                                    <div className="flex items-center gap-4">
                                        {song.album.images[2] && (
                                            <img
                                                src={song.album.images[2].url}
                                                alt={song.album.name}
                                                className="w-10 h-10 rounded"
                                            />
                                        )}
                                        <div>
                                            <div className="font-medium">{song.name}</div>
                                            <div className="text-sm text-gray-600">
                                                {song.artists.map(artist => artist.name).join(', ')}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            className="p-2 text-blue-600 hover:bg-blue-50 rounded-full"
                                            title="Create link"
                                        >
                                            <Link size={20} />
                                        </button>
                                        <button
                                            onClick={() => removeSong(song.id)}
                                            className="p-2 text-red-600 hover:bg-red-50 rounded-full"
                                        >
                                            <Trash2 size={20} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

export default SpotifyDashboard;