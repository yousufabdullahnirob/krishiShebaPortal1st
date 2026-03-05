import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Leaf, User, ShieldCheck, ShoppingBag } from 'lucide-react';

const Register = () => {
  const [formData, setFormData] = useState({
    identifier: '',
    password: '',
    name: '',
    role: 'farmer'
  });
  const [error, setError] = useState('');
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await register(formData);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed');
    }
  };

  const roles = [
    { id: 'farmer', label: 'Farmer', icon: Leaf },
    { id: 'buyer', label: 'Buyer', icon: ShoppingBag },
    { id: 'expert', label: 'Expert', icon: ShieldCheck },
  ];

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl border border-slate-200 p-8">
        <div className="flex flex-col items-center mb-8">
          <div className="p-3 bg-primary-100 rounded-2xl text-primary-600 mb-4">
            <Leaf size={40} fill="currentColor" />
          </div>
          <h1 className="text-3xl font-bold text-slate-900 leading-tight">Create Account</h1>
          <p className="text-slate-500 mt-2">Join the Bangladesh agritech revolution</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-100 text-red-600 rounded-xl text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">Full Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-primary-500 outline-none transition-all"
                placeholder="John Doe"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1">Phone or Email</label>
              <input
                type="text"
                value={formData.identifier}
                onChange={(e) => setFormData({ ...formData, identifier: e.target.value })}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-primary-500 outline-none transition-all"
                placeholder="017xxxxxxxx"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-3">I am a...</label>
            <div className="grid grid-cols-3 gap-4">
              {roles.map((role) => (
                <button
                  key={role.id}
                  type="button"
                  onClick={() => setFormData({ ...formData, role: role.id })}
                  className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all ${
                    formData.role === role.id
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-slate-100 hover:border-slate-200 text-slate-500'
                  }`}
                >
                  <role.icon size={24} />
                  <span className="text-sm font-bold">{role.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1">Password</label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-primary-500 outline-none transition-all"
              placeholder="••••••••"
              required
            />
          </div>

          <button type="submit" className="w-full btn-primary py-4 text-lg shadow-lg shadow-primary-200">
            Get Started
          </button>
        </form>

        <p className="mt-8 text-center text-slate-600">
          Already have an account?{' '}
          <Link to="/login" className="text-primary-600 font-bold hover:underline">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Register;
