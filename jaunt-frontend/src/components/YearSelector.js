import React, { useState, useEffect } from 'react';

const YearSelector = () => {
  // State to store our years data
  const [years, setYears] = useState([]);
  // State to track loading status
  const [isLoading, setIsLoading] = useState(true);
  // State to track any errors
  const [error, setError] = useState(null);
  // State for selected year
  const [selectedYear, setSelectedYear] = useState(null);

  // useEffect hook to fetch data when component mounts
  useEffect(() => {
    console.log('API URL:', process.env.REACT_APP_API_URL);
    fetchYears();
  }, []); // Empty dependency array means this runs once when component mounts

  // Function to fetch years from your API
  const fetchYears = async () => {
    try {
      setIsLoading(true);
      const apiURL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

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

  // Handler for when user selects a year
  const handleYearChange = (event) => {
    setSelectedYear(event.target.value);
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="text-red-500 p-4">
        Error: {error}
      </div>
    );
  }

  // Main render
  return (
    <div className="p-4">
      <label className="block text-sm font-medium mb-2">
        Select Year
      </label>
      <select
        value={selectedYear || ''}
        onChange={handleYearChange}
        className="w-full p-2 border rounded bg-white"
      >
        {years.map((year) => (
          <option key={year} value={year}>
            {year}
          </option>
        ))}
      </select>
      {selectedYear && (
        <p className="mt-4">
          Selected year: {selectedYear}
        </p>
      )}
    </div>
  );
};

export default YearSelector;