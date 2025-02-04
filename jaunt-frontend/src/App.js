// src/App.js
import React from 'react';
import YearSelector from './components/YearSelector';
import './App.css';
import DebugInfo from './components/DebugInfo';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Jaunt Stream</h1>
        <YearSelector />
      </header>
      <DebugInfo />
    </div>
  );
}

export default App;