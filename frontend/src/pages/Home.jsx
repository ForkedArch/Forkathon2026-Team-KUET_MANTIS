import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import GodsEyeMap from '../components/map/GodsEyeMap';
import { useDashboard } from '../components/layout/DashboardLayout';

export default function Home() {
  const {
    search,
    category,
    listingType,
    isPinMode,
    pinpointCoords,
    onSelectLocation,
    onCancelPinMode,
    onRequestBorrow,
    onOpenAddModal
  } = useDashboard();

  const [selectedItemId, setSelectedItemId] = useState(null);
  const navigate = useNavigate();

  const { data: items = [], isLoading } = useQuery({
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

  return (
    <div className="w-full h-full overflow-y-auto bg-slate-50 flex flex-col">
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 w-full py-16 sm:py-24 px-4 flex flex-col items-center text-center">
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-slate-900 tracking-tight max-w-4xl leading-tight">
          <span className="text-blue-600">Share More,</span> Spend Less
        </h1>
        <p className="mt-6 text-lg sm:text-xl text-slate-600 max-w-2xl">
          Empowering the KUET community to lend and borrow with ease. Build trust, earn Karma, and make the most of campus resources.
        </p>
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <button
            onClick={() => navigate('/items')}
            className="px-8 py-3.5 rounded-full bg-blue-600 text-white font-bold shadow-md hover:bg-blue-700 transition"
          >
            Find Items to Borrow
          </button>
          <button
            onClick={onOpenAddModal}
            className="px-8 py-3.5 rounded-full bg-white text-blue-700 font-bold shadow-sm border border-blue-200 hover:bg-blue-50 transition"
          >
            List Your Items
          </button>
        </div>
      </div>

      {/* God's Eye Map Section */}
      <div className="w-full max-w-7xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-slate-900">Campus Map</h2>
          <p className="text-slate-500 mt-2">Discover items available right now across the KUET campus.</p>
        </div>
        <div className="w-full h-[500px] rounded-3xl overflow-hidden shadow-sm border border-slate-200 relative">
          <GodsEyeMap
            items={items}
            selectedItemId={selectedItemId}
            isPinMode={isPinMode}
            pinpointCoords={pinpointCoords}
            onSelectLocation={onSelectLocation}
            onCancelPinMode={onCancelPinMode}
            onSelectItem={(item) => setSelectedItemId(item.id)}
            onRequestBorrow={onRequestBorrow}
            activeTypeFilter={listingType}
            activeCategoryFilter={category}
            searchQuery={search}
            className="w-full h-full"
          />
          <div className="absolute top-4 left-4 z-10 hidden sm:flex items-center gap-2 bg-white/90 backdrop-blur-md px-3.5 py-1.5 rounded-full border border-slate-200/80 shadow-sm text-xs text-slate-700">
            <span className="w-2 h-2 rounded-full bg-blue-500"></span>
            <span className="font-semibold">
              {isLoading ? 'Scanning campus...' : `${items.length} Active Items on KUET Map`}
            </span>
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="bg-white w-full py-16 px-4 border-t border-slate-100">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-slate-900">How It Works</h2>
            <p className="text-slate-500 mt-2">Our platform makes it easy to borrow and lend items with trust.</p>
          </div>
          <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
            <div className="bg-slate-50 rounded-3xl p-8 border border-slate-100 relative">
              <h3 className="text-xl font-bold text-slate-800 flex items-center gap-2 mb-6">
                <span className="text-blue-500">💳</span> Borrowing Items
              </h3>
              <ul className="space-y-6">
                <li className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold shrink-0">1</div>
                  <div>
                    <h4 className="font-bold text-slate-800">Browse Listings</h4>
                    <p className="text-sm text-slate-500 mt-1">Explore our verified campus listings to find exactly what you need.</p>
                  </div>
                </li>
                <li className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold shrink-0">2</div>
                  <div>
                    <h4 className="font-bold text-slate-800">Request & Connect</h4>
                    <p className="text-sm text-slate-500 mt-1">Send a borrow request and coordinate via 1:1 chat.</p>
                  </div>
                </li>
                <li className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold shrink-0">3</div>
                  <div>
                    <h4 className="font-bold text-slate-800">Verify Handover</h4>
                    <p className="text-sm text-slate-500 mt-1">Use a secure OTP/QR code to confirm physical item exchange.</p>
                  </div>
                </li>
              </ul>
            </div>
            
            <div className="bg-indigo-50/50 rounded-3xl p-8 border border-indigo-100 relative">
              <h3 className="text-xl font-bold text-slate-800 flex items-center gap-2 mb-6">
                <span className="text-indigo-500">➕</span> Listing Your Items
              </h3>
              <ul className="space-y-6">
                <li className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-indigo-200 text-indigo-800 flex items-center justify-center font-bold shrink-0">1</div>
                  <div>
                    <h4 className="font-bold text-slate-800">Create a Listing</h4>
                    <p className="text-sm text-slate-600 mt-1">Add details, photos, and drop a pin on the campus map.</p>
                  </div>
                </li>
                <li className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-indigo-200 text-indigo-800 flex items-center justify-center font-bold shrink-0">2</div>
                  <div>
                    <h4 className="font-bold text-slate-800">Respond to Requests</h4>
                    <p className="text-sm text-slate-600 mt-1">Accept requests from verified students and arrange handover.</p>
                  </div>
                </li>
                <li className="flex gap-4">
                  <div className="w-8 h-8 rounded-full bg-indigo-200 text-indigo-800 flex items-center justify-center font-bold shrink-0">3</div>
                  <div>
                    <h4 className="font-bold text-slate-800">Earn Karma</h4>
                    <p className="text-sm text-slate-600 mt-1">Collect +10 KUET Karma for every successful completed lend.</p>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Karma System Explained Section */}
      <div className="bg-slate-50 w-full py-16 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-slate-900">Karma System Explained</h2>
          <p className="text-slate-500 mt-2 mb-12">Our Karma system enables a true sharing economy where your contributions are rewarded.</p>
          
          <div className="grid sm:grid-cols-3 gap-8">
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
              <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto text-xl mb-4">➕</div>
              <h4 className="font-bold text-slate-800">Earn Karma</h4>
              <p className="text-sm text-slate-500 mt-2">Earn +10 Karma when others borrow your items, and +5 Karma when you return borrowed items on time.</p>
            </div>
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
              <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto text-xl mb-4">🛡️</div>
              <h4 className="font-bold text-slate-800">Gain Trust</h4>
              <p className="text-sm text-slate-500 mt-2">Build trust through successful transactions. New verified students start with 100 Base Karma.</p>
            </div>
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
              <div className="w-12 h-12 bg-rose-100 text-rose-600 rounded-full flex items-center justify-center mx-auto text-xl mb-4">⚠️</div>
              <h4 className="font-bold text-slate-800">Maintain Integrity</h4>
              <p className="text-sm text-slate-500 mt-2">Returning items late incurs a -30 Karma penalty. Keep your score high to borrow seamlessly.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer / FAQ / Support */}
      <div className="bg-slate-900 w-full py-12 px-4 text-center text-slate-400">
        <div className="max-w-3xl mx-auto">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-2">Still have questions?</h2>
            <p className="text-sm">We're here to help! Our student support team is ready to assist you.</p>
            <button className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-500 transition">Contact Support</button>
          </div>
          <div className="border-t border-slate-800 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm">
            <div className="flex items-center gap-2 font-bold text-white">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-white">K</div>
              CampusShare KUET
            </div>
            <p>&copy; 2026 KUET_MANTIS. All rights reserved.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
