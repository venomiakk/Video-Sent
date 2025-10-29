import React, { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import { useAuth } from '../context/AuthContext';
import './AnalysisApp.css';

const SOCKET_URL = 'http://localhost:8000';

function AnalysisApp() {
  const { user, isAuthenticated } = useAuth();
  const [socket, setSocket] = useState(null);
  const [analyses, setAnalyses] = useState([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [videoUrl, setVideoUrl] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [steps, setSteps] = useState([]);
  const [currentAnalysisId, setCurrentAnalysisId] = useState(null);
  const stepsEndRef = useRef(null);

  useEffect(() => {
    // Only connect if user is authenticated
    if (!isAuthenticated) {
      console.warn('No auth token found - user not logged in');
      setSocket(null);
      return;
    }

    // Get auth token
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      console.warn('No access_token in localStorage');
      setSocket(null);
      return;
    }

    console.log('Initializing Socket.IO connection with token');

    // Connect to Socket.IO with auth token
    const newSocket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      auth: {
        token: token
      },
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      timeout: 60000  // 60 sekund timeout
    });

    newSocket.on('connect', () => {
      console.log('✅ Connected to server');
      // Request list of analyses with token
      newSocket.emit('get_analyses', { token });
    });

    newSocket.on('connected', (data) => {
      console.log('Server says:', data.message);
    });

    newSocket.on('analyses_list', (data) => {
      console.log('Received analyses:', data.analyses);
      setAnalyses(data.analyses || []);
    });

    newSocket.on('analysis_step', (data) => {
      console.log('Analysis step:', data);
      setSteps(prev => [...prev, data.step]);
      setCurrentAnalysisId(data.analysis_id);
      scrollToBottom();
    });

    newSocket.on('analysis_complete', (data) => {
      console.log('Analysis complete:', data);
      setIsProcessing(false);
      const completedAnalysis = {
        id: data.analysis_id,
        title: data.title,
        transcription: data.transcription,
        sentiment: data.sentiment,
        status: 'completed'
      };
      setSelectedAnalysis(completedAnalysis);
      setSteps([]); // Wyczyść kroki i przejdź do wyników
      // Refresh analyses list with token
      newSocket.emit('get_analyses', { token });
    });

    newSocket.on('analysis_error', (data) => {
      console.error('Analysis error:', data);
      setIsProcessing(false);
      setSteps(prev => [...prev, {
        step: 'error',
        status: 'error',
        message: `Błąd: ${data.error}`,
        timestamp: new Date().toISOString()
      }]);
    });

    newSocket.on('connect_error', (error) => {
      console.error('Connection error:', error);
    });

    newSocket.on('reconnect', (attemptNumber) => {
      console.log('Reconnected after', attemptNumber, 'attempts');
      // Po reconnect pobierz listę analiz
      const token = localStorage.getItem('access_token');
      if (token) {
        newSocket.emit('get_analyses', { token });
      }
    });

    newSocket.on('reconnect_attempt', (attemptNumber) => {
      console.log('Reconnection attempt', attemptNumber);
    });

    newSocket.on('disconnect', (reason) => {
      console.log('Disconnected from server. Reason:', reason);
      if (reason === 'io server disconnect') {
        // Server disconnected - try to reconnect manually
        console.log('Server disconnected, attempting to reconnect...');
        newSocket.connect();
      }
    });

    setSocket(newSocket);

    return () => {
      console.log('Cleaning up socket connection');
      newSocket.close();
    };
  }, [isAuthenticated]); // Re-run when authentication status changes

  const scrollToBottom = () => {
    stepsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleStartAnalysis = () => {
    if (!videoUrl.trim()) {
      alert('Proszę podać URL filmu');
      return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      alert('Brak tokenu autoryzacji. Zaloguj się ponownie.');
      window.location.href = '/login';
      return;
    }

    if (!socket || !socket.connected) {
      console.error('Socket not connected. Socket state:', socket);
      alert('Brak połączenia z serwerem. Odśwież stronę i spróbuj ponownie.');
      // Try to reconnect
      window.location.reload();
      return;
    }

    console.log('Starting analysis for URL:', videoUrl);
    setIsProcessing(true);
    setSteps([]);
    setSelectedAnalysis(null);
    
    socket.emit('start_analysis', {
      url: videoUrl,
      model: 'whisperpy-base',
      token: token
    });
  };

  const handleSelectAnalysis = (analysis) => {
    setSelectedAnalysis(analysis);
    setSteps([]);
    setCurrentAnalysisId(analysis.id);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return '⏳';
      case 'in_progress': return '⚙️';
      case 'completed': return '✅';
      case 'error': return '❌';
      default: return '📝';
    }
  };

  const renderSentimentBar = (sentiment) => {
    if (!sentiment || !sentiment.message) return null;
    
    // Wyświetl analizę dla każdej kategorii
    return (
      <div className="sentiment-categories">
        {Object.entries(sentiment.message).map(([category, data]) => {
          if (!data.sentiments || data.sentiments.length === 0) return null;
          
          // Policz sentymenty
          const counts = { pozytywny: 0, negatywny: 0, neutralny: 0 };
          data.sentiments.forEach(item => {
            counts[item.sentiment] = (counts[item.sentiment] || 0) + 1;
          });
          
          const total = data.sentiments.length;
          const positive = counts.pozytywny / total;
          const negative = counts.negatywny / total;
          const neutral = counts.neutralny / total;
          
          return (
            <div key={category} className="category-sentiment">
              <h4>{category.charAt(0).toUpperCase() + category.slice(1)}</h4>
              <div className="sentiment-bars">
                <div className="sentiment-bar">
                  <span className="sentiment-label">Pozytywny</span>
                  <div className="bar-container">
                    <div className="bar positive" style={{ width: `${positive * 100}%` }}></div>
                  </div>
                  <span className="sentiment-value">{(positive * 100).toFixed(1)}%</span>
                </div>
                <div className="sentiment-bar">
                  <span className="sentiment-label">Neutralny</span>
                  <div className="bar-container">
                    <div className="bar neutral" style={{ width: `${neutral * 100}%` }}></div>
                  </div>
                  <span className="sentiment-value">{(neutral * 100).toFixed(1)}%</span>
                </div>
                <div className="sentiment-bar">
                  <span className="sentiment-label">Negatywny</span>
                  <div className="bar-container">
                    <div className="bar negative" style={{ width: `${negative * 100}%` }}></div>
                  </div>
                  <span className="sentiment-value">{(negative * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="analysis-app">
      {/* Sidebar - Lista analiz */}
      <div className="sidebar">
        <div className="sidebar-header">
          <h2>📊 Analizy NLP</h2>
          <button 
            className="new-analysis-btn"
            onClick={() => {
              setSelectedAnalysis(null);
              setSteps([]);
              setVideoUrl('');
            }}
          >
            + Nowa analiza
          </button>
        </div>

        <div className="analyses-list">
          {analyses.length === 0 ? (
            <div className="empty-state">
              <p>Brak analiz</p>
              <p className="empty-hint">Rozpocznij nową analizę</p>
            </div>
          ) : (
            analyses.map((analysis) => (
              <div
                key={analysis.id}
                className={`analysis-item ${selectedAnalysis?.id === analysis.id ? 'active' : ''}`}
                onClick={() => handleSelectAnalysis(analysis)}
              >
                <div className="analysis-icon">{getStatusIcon(analysis.status)}</div>
                <div className="analysis-info">
                  <div className="analysis-title">
                    {analysis.title || 'Bez tytułu'}
                  </div>
                  <div className="analysis-url">{analysis.url}</div>
                  <div className="analysis-date">
                    {new Date(analysis.created_at).toLocaleDateString('pl-PL')}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {(isProcessing || steps.length > 0) ? (
          // Processing Steps
          <div className="processing-view">
            <h2>Przetwarzanie analizy...</h2>
            <div className="current-step">
              {steps.length > 0 && steps[steps.length - 1].status !== 'error' && (
                <div className="current-step-indicator">
                  <div className="spinner"></div>
                  <span>{steps[steps.length - 1].message}</span>
                </div>
              )}
            </div>
            <div className="steps-container">
              {steps.map((step, index) => (
                <div key={index} className={`step-item ${step.status}`}>
                  <div className="step-icon">
                    {step.status === 'in_progress' ? '⚙️' : 
                     step.status === 'completed' ? '✅' : 
                     step.status === 'error' ? '❌' : '📝'}
                  </div>
                  <div className="step-content">
                    <div className="step-message">{step.message}</div>
                    <div className="step-time">
                      {new Date(step.timestamp).toLocaleTimeString('pl-PL')}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={stepsEndRef} />
            </div>
          </div>
        ) : selectedAnalysis ? (
          // Analysis Results
          <div className="results-view">
            <div className="results-header">
              <h1>{selectedAnalysis.title || 'Analiza'}</h1>
              <span className="status-badge">
                {getStatusIcon(selectedAnalysis.status)} {selectedAnalysis.status}
              </span>
            </div>

            {selectedAnalysis.transcription && (
              <div className="result-section">
                <h2>📝 Transkrypcja</h2>
                <div className="transcription-box">
                  {selectedAnalysis.transcription}
                </div>
              </div>
            )}

            {selectedAnalysis.sentiment && (
              <div className="result-section">
                <h2>💭 Analiza Sentymentu</h2>
                {renderSentimentBar(selectedAnalysis.sentiment)}
              </div>
            )}
          </div>
        ) : (
          // New Analysis Form - Welcome Screen
          <div className="welcome-screen">
            <div className="welcome-content">
              <h1>Analiza NLP Filmików</h1>
              <p>Wklej link do filmu YouTube, aby rozpocząć analizę sentymentu</p>

              <div className="input-section">
                <input
                  type="text"
                  value={videoUrl}
                  onChange={(e) => setVideoUrl(e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=..."
                  className="url-input"
                  disabled={isProcessing}
                />
                <button
                  onClick={handleStartAnalysis}
                  disabled={isProcessing || !videoUrl.trim()}
                  className="analyze-btn"
                >
                  {isProcessing ? 'Przetwarzanie...' : 'Rozpocznij analizę'}
                </button>
              </div>

              <div className="features">
                <div className="feature">
                  <span className="feature-icon">📥</span>
                  <span>Pobieranie wideo</span>
                </div>
                <div className="feature">
                  <span className="feature-icon">🎤</span>
                  <span>Transkrypcja audio</span>
                </div>
                <div className="feature">
                  <span className="feature-icon">💭</span>
                  <span>Analiza sentymentu</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default AnalysisApp;
