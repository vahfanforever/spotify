import React, { useState, useEffect } from 'react';
import { Search, Plus, Save } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';

const SpotifyDashboard = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [selectedSongs, setSelectedSongs] = useState([]);
    const [isSearching, setIsSearching] = useState(false);
    const [error, setError] = useState(null);
    const [saveSuccess, setSaveSuccess] = useState(false);
    const [relationships, setRelationships] = useState({});

    // Clear selected songs
    const clearSelectedSongs = () => {
        setSelectedSongs([]);
    };

    // Function to handle drag and drop
    const onDragEnd = (result) => {
        if (!result.destination) return;

        const items = Array.from(selectedSongs);
        const [reorderedItem] = items.splice(result.source.index, 1);
        items.splice(result.destination.index, 0, reorderedItem);

        setSelectedSongs(items);
    };

    // Function to search songs using Spotify API
    const searchSongs = async () => {
        if (!searchQuery.trim()) return;

        setIsSearching(true);
        setError(null);

        try {
            const response = await fetch(`http://localhost:8000/api/v1/search?q=${encodeURIComponent(searchQuery)}`, {
                credentials: 'include'
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

    // Function to save song relationships
    const saveRelationships = async () => {
        if (selectedSongs.length < 2) {
            setError("Please select at least 2 songs to create a group.");
            setTimeout(() => {
                setError(null);
            }, 3000);
            return;
        }

        try {
            const response = await fetch('http://localhost:8000/api/v1/songs/relationships', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    songs: selectedSongs
                })
            });

            if (!response.ok) throw new Error('Failed to save relationships');

            const data = await response.json();
            setRelationships(data.relationships);
            setSaveSuccess(true);

            // Clear the selected songs list immediately after successful save
            clearSelectedSongs();

            // Clear the success message after 3 seconds
            setTimeout(() => {
                setSaveSuccess(false);
            }, 3000);
        } catch (err) {
            setError(err.message);
            console.error('Save error:', err);
        }
    };


    return (
        <div className="p-6 min-h-screen bg-gray-50">
            <div className="max-w-7xl mx-auto">
                <div className="flex justify-between items-center mb-6">
                    <h1 className="text-2xl font-bold">Link Your Songs</h1>
                    {selectedSongs.length > 0 && (
                        <button
                            onClick={saveRelationships}
                            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-2"
                        >
                            <Save size={20} />
                            Save Order
                        </button>
                    )}
                </div>

                {saveSuccess && (
                    <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
                        <p className="text-green-700">Song relationships saved successfully!</p>
                    </div>
                )}

                {error && (
                    <div className="p-4 mb-4 text-red-700 bg-red-100 rounded-md">
                        {error}
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Search Section */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Search Songs</CardTitle>
                        </CardHeader>
                        <CardContent>
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

                            <div className="space-y-2 max-h-[60vh] overflow-y-auto">
                                {searchResults.map(song => (
                                    <div key={song.id} className="flex items-center justify-between p-3 bg-white rounded-md shadow-sm">
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
                        </CardContent>
                    </Card>

                    {/* Selected Songs Section */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Selected Songs</CardTitle>
                            <div className="text-sm text-gray-500">
                                Place them in the order you would like them to play
                            </div>
                        </CardHeader>
                        <CardContent>
                            <DragDropContext onDragEnd={onDragEnd}>
                                <Droppable droppableId="selected-songs">
                                    {(provided, snapshot) => (
                                        <div
                                            {...provided.droppableProps}
                                            ref={provided.innerRef}
                                            className={`space-y-2 min-h-[200px] max-h-[60vh] overflow-y-auto p-2 rounded-md ${snapshot.isDraggingOver ? 'bg-blue-50' : ''
                                                }`}
                                        >
                                            {selectedSongs.map((song, index) => (
                                                <Draggable
                                                    key={song.id}
                                                    draggableId={song.id}
                                                    index={index}
                                                >
                                                    {(provided, snapshot) => (
                                                        <div
                                                            ref={provided.innerRef}
                                                            {...provided.draggableProps}
                                                            {...provided.dragHandleProps}
                                                            className={`p-3 bg-white rounded-md shadow-sm ${snapshot.isDragging ? 'shadow-lg ring-2 ring-blue-500' : ''
                                                                }`}
                                                        >
                                                            <div className="flex items-center gap-4">
                                                                <div className="text-gray-400 select-none">
                                                                    {index + 1}
                                                                </div>
                                                                {song.album.images[2] && (
                                                                    <img
                                                                        src={song.album.images[2].url}
                                                                        alt={song.album.name}
                                                                        className="w-10 h-10 rounded"
                                                                    />
                                                                )}
                                                                <div className="flex-1">
                                                                    <div className="font-medium">{song.name}</div>
                                                                    <div className="text-sm text-gray-600">
                                                                        {song.artists.map(artist => artist.name).join(', ')}
                                                                    </div>
                                                                </div>
                                                                <button
                                                                    onClick={() => removeSong(song.id)}
                                                                    className="p-2 text-red-600 hover:bg-red-50 rounded-full"
                                                                >
                                                                    ×
                                                                </button>
                                                            </div>
                                                        </div>
                                                    )}
                                                </Draggable>
                                            ))}
                                            {provided.placeholder}
                                        </div>
                                    )}
                                </Droppable>
                            </DragDropContext>

                            {selectedSongs.length === 0 && (
                                <div className="text-center text-gray-500 py-8">
                                    Add songs from the search results to create your sequence
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default SpotifyDashboard;