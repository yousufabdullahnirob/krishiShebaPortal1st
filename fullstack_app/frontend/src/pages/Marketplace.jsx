import React, { useState, useEffect } from 'react';
import client from '../api/client';
import { ShoppingBag, Tag, MapPin, Plus, Filter } from 'lucide-react';

const Marketplace = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPosts();
  }, []);

  const fetchPosts = async () => {
    try {
      const res = await client.get('/api/market/');
      setPosts(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <header className="flex justify-between items-center text-slate-900 border-none bg-white p-6 rounded-2xl shadow-sm">
        <div>
          <h1 className="text-3xl font-bold">Agricultural Marketplace</h1>
          <p className="text-slate-500 mt-1">Direct trading between farmers and buyers.</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Plus size={18} />
          Post Product
        </button>
      </header>

      <div className="flex gap-4 items-center">
        <button className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-slate-600 text-sm font-medium hover:bg-slate-50">
          <Filter size={16} />
          All Categories
        </button>
        <button className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl text-slate-600 text-sm font-medium hover:bg-slate-50">
          Price Range
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {posts.map((post) => (
          <div key={post.id} className="card p-0 overflow-hidden group">
            <div className="h-48 bg-slate-100 relative">
              {post.image ? (
                <img src={post.image} alt={post.crop_name} className="w-full h-full object-cover" />
              ) : (
                <div className="flex items-center justify-center h-full text-slate-300">
                  <ShoppingBag size={48} />
                </div>
              )}
              <div className="absolute top-4 right-4 bg-white/90 backdrop-blur px-3 py-1 rounded-full text-sm font-bold text-primary-700 shadow-sm">
                ৳{post.price}/kg
              </div>
            </div>
            
            <div className="p-6">
              <div className="flex justify-between items-start mb-2">
                <h4 className="text-xl font-bold text-slate-800">{post.crop_name}</h4>
                <div className="flex items-center gap-1 text-slate-400 text-sm">
                  <Tag size={14} />
                  <span>{post.quantity}kg avail.</span>
                </div>
              </div>
              
              <div className="flex items-center gap-1 text-slate-500 text-sm mb-4">
                <MapPin size={14} />
                <span>{post.farmer_region || 'Bangladesh'}</span>
              </div>

              <div className="flex items-center gap-4 pt-4 border-t border-slate-100">
                <button className="flex-1 btn-primary bg-primary-50 text-primary-700 hover:bg-primary-100">
                  Contact Seller
                </button>
                <button className="flex-1 btn-primary">
                  Order Now
                </button>
              </div>
            </div>
          </div>
        ))}

        {posts.length === 0 && !loading && (
          <div className="col-span-full py-20 text-center bg-white rounded-2xl border-2 border-dashed border-slate-200">
            <ShoppingBag size={48} className="mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500">No products available in the marketplace right now.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Marketplace;
