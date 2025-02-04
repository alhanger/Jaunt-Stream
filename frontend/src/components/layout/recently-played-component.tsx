import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { Play, Clock, Calendar } from 'lucide-react';

const RecentlyPlayed = ({ onPlaySong }) => {
  const [recentlyPlayed, setRecentlyPlayed] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [timeFilter, setTimeFilter] = useState('all'); // all, week, month

  useEffect(() => {
    fetchRecentlyPlayed();
  }, [timeFilter]);

  const fetchRecentlyPlayed = async () => {
    try {
      setIsLoading(true);
      const days = timeFilter === 'week' ? 7 : timeFilter === 'month' ? 30 : undefined;
      const response = await fetch(`/api/recently-played?days=${days || ''}`);
      const data = await response.json();
      setRecentlyPlayed(data);
    } catch (error) {
      console.error('Error fetching recently played:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDuration = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Recently Played</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setTimeFilter('all')}
            className={`px-4 py-2 rounded ${
              timeFilter === 'all' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            All Time
          </button>
          <button
            onClick={() => setTimeFilter('month')}
            className={`px-4 py-2 rounded ${
              timeFilter === 'month' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            Past Month
          </button>
          <button
            onClick={() => setTimeFilter('week')}
            className={`px-4 py-2 rounded ${
              timeFilter === 'week' ? 'bg-blue-600' : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            Past Week
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <div className="space-y-4">
          {recentlyPlayed.map((item) => (
            <div
              key={`${item.song.id}-${item.played_at}`}
              className="flex items-center justify-between p-4 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors"
            >
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => onPlaySong(item.song.id)}
                  className="p-2 rounded-full hover:bg-blue-600 transition-colors"
                >
                  <Play size={20} />
                </button>
                <div>
                  <h3 className="font-medium">{item.song.name}</h3>
                  <div className="text-sm text-gray-400 flex items-center gap-2">
                    <Calendar size={14} />
                    <span>
                      {format(new Date(item.show.date), 'MMM d, yyyy')} - {item.show.venue}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-4 text-gray-400">
                <div className="flex items-center space-x-1">
                  <Clock size={14} />
                  <span>{formatDuration(item.song.duration)}</span>
                </div>
                <span className="text-sm">
                  {format(new Date(item.played_at), 'MMM d, h:mm a')}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RecentlyPlayed;