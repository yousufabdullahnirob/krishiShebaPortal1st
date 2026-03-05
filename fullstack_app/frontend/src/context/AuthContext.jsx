import React, { createContext, useContext, useState, useEffect } from 'react';
import {jwtDecode} from 'jwt-decode';
import client from '../api/client';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const decoded = jwtDecode(token);
        if (decoded.exp * 1000 < Date.now()) {
          logout();
        } else {
          // In a real app, fetch user profile here
          setUser({ username: decoded.username, role: decoded.role });
        }
      } catch (err) {
        logout();
      }
    }
    setLoading(false);
  }, []);

  const login = async (identifier, password) => {
    const response = await client.post('/api/login/', { identifier, password });
    const { token, refresh, user: userData } = response.data;
    localStorage.setItem('token', token);
    localStorage.setItem('refresh', refresh);
    setUser(userData);
    return userData;
  };

  const register = async (data) => {
    const response = await client.post('/api/register/', data);
    const { token, refresh, user: userData } = response.data;
    localStorage.setItem('token', token);
    localStorage.setItem('refresh', refresh);
    setUser(userData);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
