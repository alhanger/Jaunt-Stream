import React, { useState, useEffect } from 'react';
import { Calendar, Search, ChevronDown, Play, Plus } from 'lucide-react';
import { format } from 'date-fns';
import { useApi } from '../services/api';

const ShowBrowser = ({ onPlayTrack, onAddToQueue }) => {
  const [years, setYears] = useState([]);
  const [selectedYear, setSelectedYear] = useState(null);
  const [shows, setShows] = useState([]);
  const [selectedShow, setSelectedShow] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchVenue, setSearchVenue] = useState('');
  const { fetchWithAuth } = useApi();

  // Fetch available years
  useEffect(() => {
    const fetchYears = async () => {
      try {
        const response = await fetchWithAuth('/shows/years');
        setYears(response);
        if (response.length > 0) {
          setSelectedYear(response[0]);
        }
      } catch (error) {
        console.error('Error fetching years:', error);
      }
    };
    fetchYears();
  }, []);

  // Fetch shows when year changes
  useEffect(() => {
    if (selectedYear) {
      const fetchShows = async () => {
        setLoading(true);
        try {
          const response = await fetchWithAuth(`/shows/search?year=${selectedYear}&venue=${searchVenue}`);
          setShows(response);
        } catch (error) {
          console.error('Error fetching shows:', error);
        } finally {
          setLoading(false);
        }
      };
      fetchShows();
    }
  }, [selectedYear, searchVenue]);

  const fetchShowDetails = async (showId) => {
    try {
      const response = await fetchWithAuth(`/shows/${showId}`);
      setSelectedShow(response);
    } catch (error) {
      console.error('Error fetching show details:', error);
    }
  };

  return (
    <div className="flex h-full">
      {/* Show List */}
      <div className="w-1/2 border-r border-gray-800 p-4">
        <div className="mb-6 space-y-4">
          {/* Year Selector */}
          <div className="relative">
            <select 
              value={selectedYear || ''}
              onChange={(e) => setSelectedYear(e.target.value)}
              className="w-full bg-gray-800 text-white p-3 rounded appearance-none cursor-pointer"
            >
              {years.map((year) => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          </div>

          {/* Venue Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search venues..."
              value={searchVenue}
              onChange={(e) => setSearchVenue(e.target.value)}
              className="w-full bg-gray-800 text-white p-3 pl-10 rounded"
            />
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          </div>
        </div>

        {/* Shows List */}
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        ) : (
          <div className="space-y-2 overflow-y-auto max-h-[calc(100vh-300px)]">
            {shows.map((show) => (
              <button
                key={show.id}
                onClick={() => fetchShowDetails(show.id)}
                className={`w-full text-left p-4 rounded hover:bg-gray-800 transition-colors ${
                  selectedShow?.id === show.id ? 'bg-gray-800' : ''
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Calendar size={20} className="text-gray-400" />
                  <div>
                    <div className="font-medium">
                      {format(new Date(show.date), 'MMMM d, yyyy')}
                    </div>
                    <div className="text-sm text-gray-400">{show.venue}</div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Show Details */}
      <div className="w-1/2 p-4">
        {selectedShow ? (
          <div>
            <div className="mb-6">
              <h2 className="text-2xl font-bold">
                {format(new Date(selectedShow.date), 'MMMM d, yyyy')}
              </h2>
              <p className="text-lg text-gray-400">{selectedShow.venue}</p>
              <p className="text-gray-500">{selectedShow.location}</p>
            </div>

            {/* Tracks */}
            <div className="space-y-2">
              {selectedShow.tracks.map((track) => (
                <div
                  key={track.id}
                  className="flex items-center justify-between p-3 rounded hover:bg-gray-800 group"
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-gray-500">{track.name}</span>
                  </div>
                  <div className="space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => onPlayTrack(selectedShow.id, track)}
                      className="p-2 hover:bg-blue-600 rounded-full transition-colors"
                    >
                      <Play size={16} />
                    </button>
                    <button
                      onClick={() => onAddToQueue(selectedShow.id, track)}
                      className="p-2 hover:bg-blue-600 rounded-full transition-colors"
                    >
                      <Plus size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex justify-center items-center h-full text-gray-500">
            Select a show to view details
          </div>
        )}
      </div>
    </div>
  );
};

export default ShowBrowser;