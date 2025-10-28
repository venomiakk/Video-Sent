import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import AnalysisApp from './AnalysisApp';
import './Dashboard.css';

function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="dashboard-container-wrapper">
      <nav className="dashboard-nav">
        <div className="nav-brand">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <path d="M16 3C8.82 3 3 8.82 3 16s5.82 13 13 13 13-5.82 13-13S23.18 3 16 3z" fill="#10a37f"/>
            <path d="M16 9v14M9 16h14" stroke="white" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          <span>Analiza NLP</span>
        </div>
        <div className="nav-user">
          <span className="user-email">{user?.email}</span>
          <button onClick={handleLogout} className="logout-btn">
            Wyloguj się
          </button>
        </div>
      </nav>
      
      <AnalysisApp />
    </div>
  );
}

export default Dashboard;
