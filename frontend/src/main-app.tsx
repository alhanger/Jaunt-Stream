import React, { useState, useEffect, useRef } from 'react';
import { Music, Calendar, Heart, Search, Play, Pause, SkipBack, SkipForward, Volume2, VolumeX, Plus, ChevronDown, Clock } from 'lucide-react';
import { format } from 'date-fns';

// Auth0 imports
import { useAuth0 } from '@auth0/auth0-react';

const ShowBrowser = ({ onPlayTrack, onAddToQueue }) => {
  const [years, setYears] = useState([]);
  const [selectedYear, setSelectedYear] = useState(null);
  const [shows, setShows] = useState([]);
  const [selectedShow, setSelectedShow] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchVenue, setSearchVenue] = useState('');
  const { getAccessTokenSilently } = useAuth0();

  const fetchWithAuth = async (endpoint, options = {}) => {
    try {
      const token = await getAccessTokenSilently();
      const response = await fetch(`/api${endpoint}`, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) throw new Error('API Error');
      return response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  };

  // Fetch shows and years implementation...
  // (Rest of ShowBrowser implementation remains the same)

  return (
    <div className="flex h-full">
      {/* Show List */}
      <div className="w-1/2 border-r border-gray-800 p-4">
        {/* Year Selector and Search implementation... */}
      </div>
      {/* Show Details */}
      <div className="w-1/2 p-4">
        {/* Show details implementation... */}
      </div>
    </div>
  );
};

const AudioPlayer = ({ onTrackComplete }) => {
  const [currentTrack, setCurrentTrack] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [progress, setProgress] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef(null);
  const { getAccessTokenSilently } = useAuth0();

  // AudioPlayer implementation...
  // (Rest of AudioPlayer implementation remains the same)

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-800 p-4">
      {/* Audio player implementation... */}
    </div>
  );
};

const LoginButton = () => {
  const { loginWithRedirect } = useAuth0();

  return (
    <button
      onClick={() => loginWithRedirect()}
      className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded"
    >
      Log In
    </button>
  );
};

const SongPerformanceStats = ({ performances }) => {
  const calculateStats = () => {
    const totalPerformances = performances.length;
    const averageDuration = performances.reduce((acc, perf) => 
      acc + perf.song.duration, 0) / totalPerformances;
    
    const yearStats = performances.reduce((acc, perf) => {
      const year = new Date(perf.show.date).getFullYear();
      acc[year] = (acc[year] || 0) + 1;
      return acc;
    }, {});

    const maxDuration = Math.max(...performances.map(p => p.song.duration));
    const minDuration = Math.min(...performances.map(p => p.song.duration));

    return {
      totalPerformances,
      averageDuration,
      yearStats,
      maxDuration,
      minDuration
    };
  };

  const stats = calculateStats();

  return (
    <div className="bg-gray-800 rounded-lg p-4 mb-6">
      <h3 className="text-lg font-semibold mb-3">Performance Statistics</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <div className="text-gray-400 text-sm">Total Performances</div>
          <div className="text-xl font-medium">{stats.totalPerformances}</div>
        </div>
        <div>
          <div className="text-gray-400 text-sm">Average Duration</div>
          <div className="text-xl font-medium">{formatDuration(stats.averageDuration)}</div>
        </div>
        <div>
          <div className="text-gray-400 text-sm">Longest Version</div>
          <div className="text-xl font-medium">{formatDuration(stats.maxDuration)}</div>
        </div>
        <div>
          <div className="text-gray-400 text-sm">Shortest Version</div>
          <div className="text-xl font-medium">{formatDuration(stats.minDuration)}</div>
        </div>
      </div>
      <div className="mt-4">
        <div className="text-gray-400 text-sm mb-2">Performances by Year</div>
        <div className="flex flex-wrap gap-2">
          {Object.entries(stats.yearStats).sort((a, b) => b[0] - a[0]).map(([year, count]) => (
            <div key={year} className="px-3 py-1 bg-gray-700 rounded">
              {year}: {count}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const SongSearch = ({ onPlayTrack, onAddToQueue }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedSongPerformances, setSelectedSongPerformances] = useState(null);
  const { getAccessTokenSilently } = useAuth0();

  const fetchWithAuth = async (endpoint, options = {}) => {
    try {
      const token = await getAccessTokenSilently();
      const response = await fetch(`/api${endpoint}`, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) throw new Error('API Error');
      return response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  };

  const searchSongs = async () => {
    if (!searchTerm.trim()) return;
    
    setLoading(true);
    try {
      const results = await fetchWithAuth(`/songs/search?q=${encodeURIComponent(searchTerm)}`);
      setSearchResults(results);
      setSelectedSongPerformances(null);
    } catch (error) {
      console.error('Error searching songs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSongPerformances = async (songName) => {
    setLoading(true);
    try {
      const performances = await fetchWithAuth(`/songs/performances?name=${encodeURIComponent(songName)}`);
      setSelectedSongPerformances({
        name: songName,
        performances: performances
      });
    } catch (error) {
      console.error('Error fetching song performances:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (searchTerm) {
        searchSongs();
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [searchTerm]);

  const formatDuration = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const groupPerformancesByYear = (performances) => {
    return performances.reduce((acc, performance) => {
      const year = new Date(performance.show.date).getFullYear();
      if (!acc[year]) {
        acc[year] = [];
      }
      acc[year].push(performance);
      return acc;
    }, {});
  };

  const [compareMode, setCompareMode] = useState(false);
  const [selectedVersions, setSelectedVersions] = useState([]);

  const addToComparison = (performance) => {
    if (!selectedVersions.find(v => v.song.id === performance.song.id)) {
      setSelectedVersions([...selectedVersions, performance]);
    }
  };

  const removeFromComparison = (performance) => {
    setSelectedVersions(selectedVersions.filter(v => v.song.id !== performance.song.id));
  };

  const addAllToQueue = () => {
    selectedVersions.forEach(version => {
      onAddToQueue(version.show.id, version.song);
    });
  };

  const toggleVersion = (performance) => {
    if (selectedVersions.find(v => v.song.id === performance.song.id)) {
      removeFromComparison(performance);
    } else {
      addToComparison(performance);
    }
  };

  if (selectedSongPerformances) {
    const performancesByYear = groupPerformancesByYear(selectedSongPerformances.performances);
    const years = Object.keys(performancesByYear).sort((a, b) => b - a);

    return (
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold">{selectedSongPerformances.name}</h2>
            <p className="text-gray-400 mt-1">
              {selectedSongPerformances.performances.length} performances found
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => setCompareMode(!compareMode)}
              className={`px-4 py-2 rounded ${
                compareMode ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-800 hover:bg-gray-700'
              }`}
            >
              {compareMode ? 'Exit Compare' : 'Compare Versions'}
            </button>
            <button
              onClick={() => setSelectedSongPerformances(null)}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded"
            >
              Back to Search
            </button>
          </div>
        </div>
        
        <SongPerformanceStats performances={selectedSongPerformances.performances} />
        
        {compareMode && (
          <div className="mb-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-3">Version Comparison</h3>
              <div className="flex flex-wrap gap-2">
                {selectedVersions.map((version, index) => (
                  <div key={index} className="flex items-center space-x-2 bg-gray-700 px-3 py-1 rounded">
                    <span>{format(new Date(version.show.date), 'MM/dd/yyyy')}</span>
                    <button
                      onClick={() => removeFromComparison(version)}
                      className="text-gray-400 hover:text-red-500"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
              {selectedVersions.length > 0 && (
                <div className="mt-4 flex justify-end space-x-2">
                  <button
                    onClick={addAllToQueue}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
                  >
                    Add All to Queue
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="space-y-6">
          {years.map(year => (
            <div key={year} className="space-y-4">
              <h3 className="text-xl font-semibold text-gray-300">{year}</h3>
              <div className="space-y-3">
                {performancesByYear[year].map((performance) => (
                  <div
                    key={`${performance.show.id}-${performance.song.id}`}
                    className="bg-gray-800 rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="text-gray-300 flex items-center space-x-2">
                          <Calendar size={14} />
                          <span>{format(new Date(performance.show.date), 'MMMM d')}</span>
                        </div>
                        <div className="text-gray-400 mt-1">{performance.show.venue}</div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center space-x-1 text-gray-400">
                          <Clock size={14} />
                          <span>{formatDuration(performance.song.duration)}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          {compareMode && (
                            <button
                              onClick={() => toggleVersion(performance)}
                              className={`px-3 py-1 rounded text-sm ${
                                selectedVersions.find(v => v.song.id === performance.song.id)
                                  ? 'bg-blue-600 hover:bg-blue-700'
                                  : 'bg-gray-700 hover:bg-gray-600'
                              }`}
                            >
                              {selectedVersions.find(v => v.song.id === performance.song.id)
                                ? 'Selected'
                                : 'Compare'}
                            </button>
                          )}
                          <button
                            onClick={() => onPlayTrack(performance.show.id, performance.song)}
                            className="p-2 hover:bg-blue-600 rounded-full transition-colors"
                          >
                            <Play size={16} />
                          </button>
                          <button
                            onClick={() => onAddToQueue(performance.show.id, performance.song)}
                            className="p-2 hover:bg-blue-600 rounded-full transition-colors"
                          >
                            <Plus size={16} />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-4">Song Search</h2>
        <div className="relative">
          <input
            type="text"
            placeholder="Search for songs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-gray-800 text-white p-3 pl-10 rounded"
          />
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div className="space-y-4">
          {searchResults.map((result) => (
            <div
              key={`${result.show.id}-${result.song.id}`}
              className="bg-gray-800 rounded-lg p-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="font-medium text-lg">
                    <button
                      onClick={() => fetchSongPerformances(result.song.name)}
                      className="hover:text-blue-400 transition-colors"
                    >
                      {result.song.name}
                    </button>
                  </h3>
                  <div className="text-gray-400 text-sm mt-1">
                    <div className="flex items-center space-x-2">
                      <Calendar size={14} />
                      <span>{format(new Date(result.show.date), 'MMMM d, yyyy')}</span>
                    </div>
                    <div className="mt-1">{result.show.venue}</div>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-1 text-gray-400">
                    <Clock size={14} />
                    <span>{formatDuration(result.song.duration)}</span>
                  </div>
                  <div className="space-x-2">
                    <button
                      onClick={() => onPlayTrack(result.show.id, result.song)}
                      className="p-2 hover:bg-blue-600 rounded-full transition-colors"
                    >
                      <Play size={16} />
                    </button>
                    <button
                      onClick={() => onAddToQueue(result.show.id, result.song)}
                      className="p-2 hover:bg-blue-600 rounded-full transition-colors"
                    >
                      <Plus size={16} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
          {searchResults.length === 0 && searchTerm && !loading && (
            <div className="text-center text-gray-500 py-8">
              No songs found matching "{searchTerm}"
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const LogoutButton = () => {
  const { logout } = useAuth0();

  return (
    <button
      onClick={() => logout({ returnTo: window.location.origin })}
      className="bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded"
    >
      Log Out
    </button>
  );
};

const App = () => {
  const [currentView, setCurrentView] = useState('shows');
  const { isAuthenticated, user, getAccessTokenSilently } = useAuth0();
  const audioPlayerRef = useRef();

  const fetchWithAuth = async (endpoint, options = {}) => {
    try {
      const token = await getAccessTokenSilently();
      const response = await fetch(`/api${endpoint}`, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) throw new Error('API Error');
      return response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  };

  const handlePlayTrack = async (showId, track) => {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.playTrack(showId, track);
    }
  };

  const handleAddToQueue = async (showId, track) => {
    try {
      await fetchWithAuth(`/shows/${showId}/queue/${track.id}`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('Error adding to queue:', error);
    }
  };

  const handleTrackComplete = async () => {
    try {
      const response = await fetchWithAuth('/shows/queue/next');
      if (response.track) {
        handlePlayTrack(response.track.showId, response.track);
      }
    } catch (error) {
      console.error('Error getting next track:', error);
    }
  };

  const renderContent = () => {
    if (!isAuthenticated) {
      return (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-4">Welcome to The Jauntee Stream</h2>
            <p className="text-gray-400 mb-6">Please log in to access the music library</p>
            <LoginButton />
          </div>
        </div>
      );
    }

    switch (currentView) {
      case 'shows':
        return (
          <ShowBrowser
            onPlayTrack={handlePlayTrack}
            onAddToQueue={handleAddToQueue}
          />
        );
      case 'songs':
        return <SongSearch onPlayTrack={handlePlayTrack} onAddToQueue={handleAddToQueue} />;
      case 'favorites':
        return <div>Favorites View (Coming Soon)</div>;
      case 'search':
        return <div>Search View (Coming Soon)</div>;
      default:
        return null;
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-900 text-white">
      <header className="h-16 border-b border-gray-800 flex items-center justify-between px-6">
        <h1 className="text-2xl font-bold">The Jauntee Stream</h1>
        <div className="flex items-center space-x-4">
          {isAuthenticated ? (
            <>
              <div className="flex items-center space-x-2">
                <span>{user?.name}</span>
              </div>
              <LogoutButton />
            </>
          ) : (
            <LoginButton />
          )}
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <nav className="w-64 border-r border-gray-800 p-4">
          <ul className="space-y-4">
            <li>
              <button
                onClick={() => setCurrentView('shows')}
                className={`flex items-center space-x-2 w-full p-2 rounded ${
                  currentView === 'shows' ? 'bg-blue-600' : 'hover:bg-gray-800'
                }`}
              >
                <Calendar size={20} />
                <span>Shows</span>
              </button>
            </li>
            <li>
              <button
                onClick={() => setCurrentView('songs')}
                className={`flex items-center space-x-2 w-full p-2 rounded ${
                  currentView === 'songs' ? 'bg-blue-600' : 'hover:bg-gray-800'
                }`}
              >
                <Music size={20} />
                <span>Songs</span>
              </button>
            </li>
            <li>
              <button
                onClick={() => setCurrentView('favorites')}
                className={`flex items-center space-x-2 w-full p-2 rounded ${
                  currentView === 'favorites' ? 'bg-blue-600' : 'hover:bg-gray-800'
                }`}
              >
                <Heart size={20} />
                <span>Favorites</span>
              </button>
            </li>
            <li>
              <button
                onClick={() => setCurrentView('search')}
                className={`flex items-center space-x-2 w-full p-2 rounded ${
                  currentView === 'search' ? 'bg-blue-600' : 'hover:bg-gray-800'
                }`}
              >
                <Search size={20} />
                <span>Search</span>
              </button>
            </li>
          </ul>
        </nav>

        <main className="flex-1 overflow-y-auto">
          {renderContent()}
        </main>
      </div>

      {isAuthenticated && (
        <AudioPlayer
          ref={audioPlayerRef}
          onTrackComplete={handleTrackComplete}
        />
      )}
    </div>
  );
};

export default App;