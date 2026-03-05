import React, { useState, useEffect } from 'react';
import client from '../api/client';
import { Camera, Send, Clock, Search, ShieldCheck } from 'lucide-react';

const AgriDoctor = () => {
  const [problems, setProblems] = useState([]);
  const [newProblem, setNewProblem] = useState({ title: '', description: '', crop_type: '', problem_type: 'রোগ' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProblems();
  }, []);

  const fetchProblems = async () => {
    try {
      const res = await client.get('/api/problems/');
      setProblems(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await client.post('/api/problems/create/', newProblem);
      setNewProblem({ title: '', description: '', crop_type: '', problem_type: 'রোগ' });
      fetchProblems();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-bold text-slate-900">Agri-Doctor</h1>
        <p className="text-slate-500 mt-1">Get AI and expert solutions for your crop problems.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Report New Problem */}
        <section className="lg:col-span-1 border-r border-slate-100 pr-0 lg:pr-8">
          <form onSubmit={handleSubmit} className="card space-y-5 sticky top-8">
            <h3 className="text-lg font-bold">Report New Problem</h3>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Crop Name</label>
              <input
                type="text"
                value={newProblem.crop_type}
                onChange={(e) => setNewProblem({ ...newProblem, crop_type: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border border-slate-200 outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="e.g. Rice, Tomato"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Issue Title</label>
              <input
                type="text"
                value={newProblem.title}
                onChange={(e) => setNewProblem({ ...newProblem, title: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border border-slate-200 outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="e.g. Yellow leaves"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
              <textarea
                value={newProblem.description}
                onChange={(e) => setNewProblem({ ...newProblem, description: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border border-slate-200 outline-none focus:ring-2 focus:ring-primary-500 h-32"
                placeholder="Detailed description of the issue..."
                required
              ></textarea>
            </div>
            <button type="submit" className="w-full btn-primary flex items-center justify-center gap-2">
              <Send size={18} />
              Submit Case
            </button>
          </form>
        </section>

        {/* Previous Cases */}
        <section className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-bold">Recent Cases</h3>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
              <input
                type="text"
                placeholder="Search cases..."
                className="pl-10 pr-4 py-2 rounded-xl bg-white border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div className="space-y-4">
            {problems.map((problem) => (
              <div key={problem.id} className="card hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <span className="text-xs font-bold text-primary-600 tracking-widest uppercase bg-primary-50 px-2 py-1 rounded">
                      {problem.tracking_id}
                    </span>
                    <h4 className="text-lg font-bold text-slate-800 mt-2">{problem.title}</h4>
                    <p className="text-sm text-slate-500">{problem.crop_type}</p>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-xs font-bold ${
                    problem.status === 'resolved' ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'
                  }`}>
                    {problem.status.replace('_', ' ')}
                  </div>
                </div>
                <p className="text-slate-600 text-sm line-clamp-2">{problem.description}</p>
                <div className="mt-4 flex items-center justify-between text-slate-400 text-xs">
                  <div className="flex items-center gap-1">
                    <Clock size={14} />
                    <span>Reported {new Date(problem.created_at).toLocaleDateString()}</span>
                  </div>
                  {problem.assigned_expert && (
                    <div className="flex items-center gap-1 text-primary-600">
                      <ShieldCheck size={14} />
                      <span>Assigned to Expert</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {problems.length === 0 && !loading && (
              <div className="text-center py-20 bg-white rounded-2xl border-2 border-dashed border-slate-200">
                <Camera size={48} className="mx-auto text-slate-300 mb-4" />
                <p className="text-slate-500">No cases reported yet. Submit your first crop problem.</p>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
};

export default AgriDoctor;
