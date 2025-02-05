import React, { useState, useEffect } from 'react';
import { Calendar, ChevronDown } from 'lucide-react';
import { format } from 'date-fns';

const YearSelector = () => {
  // State to store our years data
  const [years, setYears] = useState([]);
  // State to track loading status
  const [isLoading, setIsLoading] = useState(true);
  // State to track any errors
  const [error, setError] = useState(null);
  // State for selected year
  const [selectedYear, setSelectedYear] = useState(null);
  // State for returned shows
  const [shows, setShows] = useState([]);
  // # of shows to display
  const[showLimit] = useState(5);

  const apiURL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

  // useEffect hook to fetch data when component mounts
  useEffect(() => {
    console.log('API URL:', process.env.REACT_APP_API_URL);
    fetchYears();
  }, []); // Empty dependency array means this runs once when component mounts

  // Function to fetch years from your API
  const fetchYears = async () => {
    try {
      setIsLoading(true);

      const fullUrl = `${apiURL}/api/shows/years`;
      console.log('Fetching from: ', fullUrl);

      const response = await fetch('/api/shows/years');
      console.log('Response status: ', response.status)

      if (!response.ok) {
        throw new Error('Failed to fetch years');
      }
      const data = await response.json();
      console.log('Response text: ', data);
      
      setYears(data);
      // Set first year as default selected if available
      if (data.length > 0) {
        setSelectedYear(data[0]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }  
  };

  const fetchShowsForYear = async (year) => {
    try{
      setIsLoading(true);

      const fullUrl = `${apiURL}/api/shows/search?year=${year}`;
      
      console.log(`Searching for all shows for year ${year}`);
      const response = await fetch(fullUrl);

      if (!response.ok) {
        throw new Error('Failed to fetch shows');
      }
      const data = await response.json();
      console.log('Response text: ', data)
      setShows(data);

    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    } 
  };

  // Handler for when user selects a year
  const handleYearChange = (event) => {
    const year = event.target.value;
    setSelectedYear(year);
    fetchShowsForYear(year);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-500 p-4">
        Error: {error}
      </div>
    );
  }

  return (
    <div className="p-4">
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">
          Select Year
        </label>
        <div className="relative">
          <select
            value={selectedYear || ''}
            onChange={handleYearChange}
            className="w-full bg-gray-800 text-white p-3 rounded appearance-none cursor-pointer"
          >
            {years.map((year) => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>
          <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
        </div>
      </div>

      <div className="space-y-4">
        {shows.slice(0,showLimit).map((show) => (
          <div
            key={show.id}
            className="bg-gray-800 rounded-lg p-4 hover:bg-gray-700 transition-colors"
          >
            <div className="flex items-center space-x-3">
              <Calendar size={20} className="text-gray-400" />
              <div>
                <div className="font-medium">
                  {format(new Date(show.date), 'MMMM d, yyyy')}
                </div>
                <div className="text-gray-400">
                  {show.venue}
                </div>
                {show.location && (
                  <div className="text-gray-500 text-sm">
                    {show.location}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {shows.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            No shows found for {selectedYear}
          </div>
        )}
      </div>
    </div>
  );
};

export default YearSelector;