import React, { useState, useEffect } from 'react';
import client from '../api/client';
import { Cloud, Thermometer, Droplets, TrendingUp, AlertTriangle, CheckCircle2 } from 'lucide-react';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [cropsHealth, setCropsHealth] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, healthRes] = await Promise.all([
          client.get('/api/stats/'),
          client.get('/api/crop-health/')
        ]);
        setStats(statsRes.data);
        setCropsHealth(healthRes.data);
      } catch (err) {
        console.error('Failed to fetch dashboard data', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="animate-pulse space-y-8">
    <div className="h-32 bg-slate-200 rounded-2xl w-full" />
    <div className="grid grid-cols-3 gap-6">
      <div className="h-40 bg-slate-200 rounded-2xl" />
      <div className="h-40 bg-slate-200 rounded-2xl" />
      <div className="h-40 bg-slate-200 rounded-2xl" />
    </div>
  </div>;

  return (
    <div className="space-y-8">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Agriculture Dashboard</h1>
          <p className="text-slate-500 mt-1">Real-time overview of your farm and market activity.</p>
        </div>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card bg-gradient-to-br from-primary-600 to-primary-700 text-white border-none">
          <p className="text-primary-100 text-sm font-medium">Total Farmers</p>
          <div className="flex items-center justify-between mt-2">
            <h2 className="text-4xl font-bold">{stats?.farmers || 0}</h2>
            <TrendingUp size={32} className="opacity-50" />
          </div>
        </div>
        <div className="card">
          <p className="text-slate-500 text-sm font-medium">Reported Problems</p>
          <div className="flex items-center justify-between mt-2">
            <h2 className="text-4xl font-bold text-slate-800">{stats?.problems || 0}</h2>
            <AlertTriangle size={32} className="text-orange-400" />
          </div>
        </div>
        <div className="card">
          <p className="text-slate-500 text-sm font-medium">Active Posts</p>
          <div className="flex items-center justify-between mt-2">
            <h2 className="text-4xl font-bold text-slate-800">{stats?.posts || 0}</h2>
            <CheckCircle2 size={32} className="text-primary-500" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Crop Health Card */}
        <section className="card space-y-4">
          <h3 className="text-lg font-bold border-b border-slate-100 pb-4">Crop Health Status</h3>
          <div className="space-y-4">
            {cropsHealth && cropsHealth.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${item.status === 'good' ? 'bg-green-500' : 'bg-orange-400'}`} />
                  <span className="font-medium">{item.crop}</span>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-500 uppercase font-bold tracking-wider">{item.status}</p>
                  <p className="text-sm font-medium">{item.problems} Problems reported</p>
                </div>
              </div>
            ))}
            {(!cropsHealth || cropsHealth.length === 0) && (
              <p className="text-center text-slate-500 py-8 italic">No active crops tracked.</p>
            )}
          </div>
        </section>

        {/* Placeholder for Weather or Trends */}
        <section className="card bg-slate-800 text-white border-none relative overflow-hidden">
          <div className="relative z-10 space-y-6">
            <div className="flex items-center gap-2 text-primary-400 font-bold uppercase tracking-widest text-xs">
              <Cloud size={16} />
              <span>Weather Insight</span>
            </div>
            <div>
              <h3 className="text-5xl font-light">31°C</h3>
              <p className="text-slate-400 mt-1">Partly Cloudy • Dhaka, BD</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-3 bg-white/5 p-3 rounded-xl">
                <Thermometer size={20} className="text-primary-400" />
                <div>
                  <p className="text-xs text-slate-500">Humidity</p>
                  <p className="font-bold">65%</p>
                </div>
              </div>
              <div className="flex items-center gap-3 bg-white/5 p-3 rounded-xl">
                <Droplets size={20} className="text-primary-400" />
                <div>
                  <p className="text-xs text-slate-500">Rainfall</p>
                  <p className="font-bold">2.4mm</p>
                </div>
              </div>
            </div>
          </div>
          <div className="absolute -right-10 -bottom-10 opacity-10">
            <Cloud size={200} />
          </div>
        </section>
      </div>
    </div>
  );
};

export default Dashboard;
