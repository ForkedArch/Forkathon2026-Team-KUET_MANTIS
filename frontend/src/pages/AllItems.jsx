import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import Loader from '../components/common/Loader';
import ItemHoverCard from '../components/items/ItemHoverCard';
import { useDashboard } from '../components/layout/DashboardLayout';

export default function AllItems() {
  const {
    search,
    category,
    listingType,
    setSearch,
    setCategory,
    setListingType,
    onRequestBorrow
  } = useDashboard();

  const navigate = useNavigate();

  const { data: items, isLoading, error } = useQuery({
    queryKey: ['items', { category, search, listingType }],
    queryFn: async () => {
      const params = {};
      if (search && search.trim() !== '') params.search = search.trim();
      if (category && category !== 'ALL') params.category = category;
      if (listingType && listingType !== 'ALL') params.type = listingType;
      const res = await api.get('/items', { params });
      return res.data;
    }
  });

  if (isLoading) return <Loader />;
  if (error) return <div className="p-8 text-center text-rose-500 font-semibold">Failed to load items.</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto h-full overflow-y-auto">
      {/* Header Bar */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Campus Listings</h1>
          <p className="text-sm text-slate-500">
            Active lending supplies and student borrow demand beacons within 700m KUET perimeter
          </p>
        </div>
        <div className="text-xs font-semibold text-slate-600 bg-white border border-slate-200 px-3 py-1.5 rounded-lg shadow-xs">
          Showing <span className="text-blue-600 font-bold">{items?.length || 0}</span> items
        </div>
      </div>

      {/* Empty State */}
      {items?.length === 0 ? (
        <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center max-w-md mx-auto my-8 shadow-xs">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
          </div>
          <h3 className="font-bold text-slate-800 text-base mb-1">No Listings Found</h3>
          <p className="text-xs text-slate-500 mb-4">
            Try adjusting your search query, category, or listing type filter.
          </p>
          <button
            onClick={() => {
              setSearch('');
              setCategory('ALL');
              setListingType('ALL');
            }}
            className="px-4 py-2 text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        /* Enterprise Cards Grid */
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5 pb-12">
          {items?.map((item) => (
            <ItemHoverCard
              key={item.id}
              item={item}
              onRequest={onRequestBorrow}
              onChat={() => navigate('/requests')}
              onFocusOnMap={() => navigate('/')}
            />
          ))}
        </div>
      )}
    </div>
  );
}
