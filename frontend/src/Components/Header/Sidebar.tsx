// Sidebar.tsx
import React from 'react';

const Sidebar: React.FC = () => {
  return (
    <nav style={sidebarStyle}>
      <ul>
        <li><a href="#">Home</a></li>
        <li><a href="#">Calendar</a></li>
        <li><a href="#">Activity</a></li>
        <li><a href="#">Wanted</a></li>
        <li><a href="#">Settings</a></li>
        <li><a href="#">System</a></li>
      </ul>
    </nav>
  );
};

const sidebarStyle: React.CSSProperties = {
    height: '100vh',
    width: '200px',
    backgroundColor: '#333',
    color: 'white',
    padding: '20px',
    position: 'fixed',
    top: 0,
    left: 0,
    display: 'flex',
    flexDirection: 'column', // Correctly typed as a valid FlexDirection
    justifyContent: 'flex-start',
  };

export default Sidebar;
