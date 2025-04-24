import React from 'react';
import logo from './logo.svg';
import Sidebar from './Components/Header/Sidebar';
import './App.css';

const App: React.FC = () => {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <div style={appStyle}>
          {/* Sidebar on the left */}
          <Sidebar />
          <p>
            Edit <code>src/App.tsx</code> and save to reload.
          </p>
          <a
            className="App-link"
            href="https://reactjs.org"
            target="_blank"
            rel="noopener noreferrer"
          >
            Learn React
          </a>
        </div>
      </header>
    </div>
  );
};

// Add React.CSSProperties to make the style object compatible with TypeScript
const appStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'row', // Valid value for flexDirection
};

const contentStyle = {
  marginLeft: '200px', // To make space for the sidebar
  padding: '20px',
  width: '100%',
};

export default App;
