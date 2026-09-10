import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import api, { API_ORIGIN } from '../api/client';
import { Link } from 'react-router-dom';
import { formatDept } from '../utils/dept';

export default function Profile() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('overview'); // overview, saved, reviews

  // Fetch Wishlisted Items
  const { data: savedItems = [], isLoading: loadingSaved } = useQuery({
    queryKey: ['saved-items'],
    queryFn: () => api.get('/items/saved/all').then((res) => res.data),
    enabled: !!user,
  });

  // Fetch Reviews
  const { data: reviews = [], isLoading: loadingReviews } = useQuery({
    queryKey: ['reviews', user?.id],
    queryFn: () => api.get(`/reviews/user/${user.id}`).then((res) => res.data),
    enabled: !!user,
  });

  if (!user) return <div className="p-8 text-center text-slate-500">Please log in to view profile.</div>;

  const karma = user.karma ?? 100;
  const netKarmaChange = karma - 100;
  const averageRating =
    reviews.length > 0
      ? (reviews.reduce((acc, r) => acc + r.rating, 0) / reviews.length).toFixed(1)
      : null;

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 space-y-6 h-full overflow-y-auto pb-16">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Student Profile & Activity</h1>
        {averageRating && (
          <span className="flex items-center gap-1 text-sm font-bold bg-amber-50 text-amber-900 border border-amber-200 px-3 py-1 rounded-full">
            ⭐ {averageRating} / 5.0 ({reviews.length} reviews)
          </span>
        )}
      </div>

      {/* Hero Karma Rating Card */}
      <div className="bg-gradient-to-r from-amber-500 via-amber-600 to-orange-600 rounded-2xl p-6 text-white shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-widest text-amber-100 block mb-1">
            KUET Karma Protocol Score
          </span>
          <div className="text-4xl font-extrabold flex items-center gap-2">
            <span>⚡ {karma}</span>
            <span className="text-sm font-medium text-amber-100 bg-white/20 px-2.5 py-0.5 rounded-full">
              {netKarmaChange >= 0 ? `+${netKarmaChange}` : netKarmaChange} from Base
            </span>
          </div>
          <p className="text-xs text-amber-100 mt-2">
            Base: 100 · +10 per lend · +5 for on-time return · -30 late penalty
          </p>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl p-3 text-center sm:text-right border border-white/20">
          <span className="text-[11px] text-amber-100 block">Exchanges Completed</span>
          <span className="text-2xl font-bold">{(user.total_lends || 0) + (user.total_borrows || 0)}</span>
          <span className="text-[10px] text-amber-200 block">({user.total_lends || 0} Lends, {user.total_borrows || 0} Borrows)</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-200 pb-1">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition ${
            activeTab === 'overview'
              ? 'bg-slate-900 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          Overview & Rules
        </button>
        <button
          onClick={() => setActiveTab('saved')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition flex items-center gap-1.5 ${
            activeTab === 'saved'
              ? 'bg-slate-900 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <span>❤️</span> Wishlist ({savedItems.length})
        </button>
        <button
          onClick={() => setActiveTab('reviews')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition flex items-center gap-1.5 ${
            activeTab === 'reviews'
              ? 'bg-slate-900 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <span>⭐</span> Reviews ({reviews.length})
        </button>
      </div>

      {/* Tab: Overview */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Academic Identity */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-3">
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
              KUET Academic Identity
            </h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Name</span>
                <span className="font-semibold text-slate-900">{user.name}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">KUET Email</span>
                <span className="font-semibold text-slate-900">{user.email}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Department</span>
                <span className="font-semibold text-slate-900">{formatDept(user.dept)}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Batch</span>
                <span className="font-semibold text-slate-900">{user.batch || '2023'}</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-slate-500">Roll Number</span>
                <span className="font-semibold text-slate-900">{user.roll || '010'}</span>
              </div>
            </div>
          </div>

          {/* Karma Protocol Rules */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-3">
            <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
              KUET Karma Rules
            </h2>
            <div className="space-y-2.5 text-xs text-slate-600">
              <div className="flex items-center justify-between p-2 rounded-lg bg-emerald-50 border border-emerald-100 text-emerald-900 font-medium">
                <span>🟢 Lending an item</span>
                <span className="font-bold">+10 Karma</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-blue-50 border border-blue-100 text-blue-900 font-medium">
                <span>⏱️ Returning on-time</span>
                <span className="font-bold">+5 Karma</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-rose-50 border border-rose-100 text-rose-900 font-medium">
                <span>⚠️ Late return penalty</span>
                <span className="font-bold">-30 Karma</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100 text-slate-700">
                <span>🛡️ Initial registration base</span>
                <span className="font-bold">100 Karma</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Saved Items */}
      {activeTab === 'saved' && (
        <div className="space-y-4">
          {loadingSaved && <p className="text-slate-400 text-sm">Loading wishlist...</p>}
          {!loadingSaved && savedItems.length === 0 && (
            <div className="p-8 text-center bg-white border border-slate-200 rounded-2xl">
              <span className="text-3xl">❤️</span>
              <p className="font-bold text-slate-800 mt-2">No saved items</p>
              <p className="text-xs text-slate-400 mt-1">Click the heart icon on any item to save it here.</p>
              <Link to="/items" className="inline-block mt-4 text-xs font-semibold text-blue-600 hover:underline">
                Browse Items
              </Link>
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {savedItems.map((item) => (
              <div key={item.id} className="bg-white rounded-xl border border-slate-200 p-3 shadow-xs flex flex-col justify-between">
                <div>
                  <h4 className="font-bold text-sm text-slate-800 truncate">{item.title}</h4>
                  <p className="text-xs text-slate-500 mt-0.5">{item.category} · 📍 {item.zone}</p>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-xs font-semibold text-emerald-600">{item.is_available ? 'Available' : 'Borrowed'}</span>
                  <Link to={`/item/${item.id}`} className="text-xs font-semibold text-blue-600 hover:underline">
                    View
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Reviews */}
      {activeTab === 'reviews' && (
        <div className="space-y-4">
          {loadingReviews && <p className="text-slate-400 text-sm">Loading reviews...</p>}
          {!loadingReviews && reviews.length === 0 && (
            <div className="p-8 text-center bg-white border border-slate-200 rounded-2xl">
              <span className="text-3xl">⭐</span>
              <p className="font-bold text-slate-800 mt-2">No reviews yet</p>
              <p className="text-xs text-slate-400 mt-1">Complete item borrowing or lending exchanges to earn student reviews.</p>
            </div>
          )}
          <div className="space-y-3">
            {reviews.map((r) => (
              <div key={r.id} className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-800">{r.reviewer?.name}</span>
                    <span className="text-xs text-slate-400">({formatDept(r.reviewer?.dept)})</span>
                  </div>
                  <div className="flex items-center text-amber-500 text-xs">
                    {'⭐'.repeat(r.rating)}
                  </div>
                </div>
                {r.comment && <p className="text-xs text-slate-600 mt-2 leading-relaxed">{r.comment}</p>}
                <span className="text-[10px] text-slate-400 mt-2 block">
                  {new Date(r.created_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
