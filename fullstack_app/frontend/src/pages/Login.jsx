import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Leaf } from 'lucide-react';

const Login = () => {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(identifier, password);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl border border-slate-200 p-8">
        <div className="flex flex-col items-center mb-8">
          <div className="p-3 bg-primary-100 rounded-2xl text-primary-600 mb-4">
            <Leaf size={40} fill="currentColor" />
          </div>
          <h1 className="text-3xl font-bold text-slate-900 leading-tight">Welcome Back</h1>
          <p className="text-slate-500 mt-2">Sign in to your Krishisheba account</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-100 text-red-600 rounded-xl text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">Phone or Email</label>
            <input
              type="text"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all"
              placeholder="e.g. 017xxxxxxxx"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all"
              placeholder="••••••••"
              required
            />
          </div>
          <button type="submit" className="w-full btn-primary py-3.5 text-lg">
            Sign In
          </button>
        </form>

        <p className="mt-8 text-center text-slate-600">
          Don't have an account?{' '}
          <Link to="/register" className="text-primary-600 font-bold hover:underline">
            Register for free
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Login;
