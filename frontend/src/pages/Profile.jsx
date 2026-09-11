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
            <span className="flex items-center gap-2">
              <svg className="w-8 h-8 text-amber-300" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
              </svg>
              <span>{karma}</span>
            </span>
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
          <svg className="w-4 h-4 text-rose-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
          </svg>
          <span>Wishlist ({savedItems.length})</span>
        </button>
        <button
          onClick={() => setActiveTab('reviews')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition flex items-center gap-1.5 ${
            activeTab === 'reviews'
              ? 'bg-slate-900 text-white'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <svg className="w-4 h-4 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
          <span>Reviews ({reviews.length})</span>
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
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-emerald-50 border border-emerald-100 text-emerald-900 font-medium">
                <span className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Lending an item</span>
                </span>
                <span className="font-bold text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded">+10 Karma</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-blue-50 border border-blue-100 text-blue-900 font-medium">
                <span className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Returning on-time</span>
                </span>
                <span className="font-bold text-blue-700 bg-blue-100/80 px-2 py-0.5 rounded">+5 Karma</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-rose-50 border border-rose-100 text-rose-900 font-medium">
                <span className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span>Late return penalty</span>
                </span>
                <span className="font-bold text-rose-700 bg-rose-100/80 px-2 py-0.5 rounded">-30 Karma</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200/80 text-slate-700 font-medium">
                <span className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <span>Initial registration base</span>
                </span>
                <span className="font-bold text-slate-700 bg-slate-200/80 px-2 py-0.5 rounded">100 Karma</span>
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
              <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-500 flex items-center justify-center mx-auto mb-2">
                <svg className="w-6 h-6 fill-current" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
                </svg>
              </div>
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
                  <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                    <span>{item.category}</span>
                    <span>·</span>
                    <svg className="w-3.5 h-3.5 text-slate-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <span>{item.zone}</span>
                  </p>
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
              <div className="w-12 h-12 rounded-full bg-amber-50 text-amber-500 flex items-center justify-center mx-auto mb-2">
                <svg className="w-6 h-6 fill-current" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              </div>
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
                  <div className="flex items-center gap-0.5 text-amber-400">
                    {Array.from({ length: r.rating || 5 }).map((_, i) => (
                      <svg key={i} className="w-3.5 h-3.5 fill-current" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
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
