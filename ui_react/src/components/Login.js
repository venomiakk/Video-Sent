import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Login.css';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let result;
      if (isLogin) {
        result = await login(email, password);
      } else {
        result = await register(email, password);
      }

      if (result.success) {
        navigate('/');
      } else {
        setError(result.error || 'Wystąpił błąd. Spróbuj ponownie.');
      }
    } catch (err) {
      setError('Wystąpił błąd połączenia z serwerem.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <div className="logo">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <path d="M16 3C8.82 3 3 8.82 3 16s5.82 13 13 13 13-5.82 13-13S23.18 3 16 3z" fill="#10a37f"/>
              <path d="M16 9v14M9 16h14" stroke="white" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <h1>{isLogin ? 'Witaj ponownie' : 'Utwórz konto'}</h1>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && <div className="error-message">{error}</div>}
          
          <div className="form-group">
            <label htmlFor="email">Adres email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="twoj@email.com"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Hasło</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? 'Proszę czekać...' : (isLogin ? 'Kontynuuj' : 'Zarejestruj się')}
          </button>
        </form>

        <div className="toggle-mode">
          {isLogin ? (
            <p>
              Nie masz konta?{' '}
              <button type="button" onClick={() => setIsLogin(false)}>
                Zarejestruj się
              </button>
            </p>
          ) : (
            <p>
              Masz już konto?{' '}
              <button type="button" onClick={() => setIsLogin(true)}>
                Zaloguj się
              </button>
            </p>
          )}
        </div>

        <div className="terms">
          <p>
            Kontynuując, zgadzasz się z naszymi{' '}
            <a href="#terms">Warunkami użytkowania</a> i{' '}
            <a href="#privacy">Polityką prywatności</a>.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
