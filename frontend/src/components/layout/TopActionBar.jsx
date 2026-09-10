import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../api/client';
import { useAuth } from '../../context/AuthContext';

const SearchIcon = () => (
  <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
);

const PlusIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 4v16m8-8H4" />
  </svg>
);

const CloseIcon = () => (
  <svg className="w-3.5 h-3.5 text-slate-400 hover:text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const MenuIcon = () => (
  <svg className="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
  </svg>
);

const CATEGORIES = [
  { id: 'ALL', label: 'All Categories', icon: '🏷️' },
  { id: 'Calculators', label: 'Calculators', icon: '🧮' },
  { id: 'Electronics & Power', label: 'Power & Chargers', icon: '🔌' },
  { id: 'Lab Equipment', label: 'Lab Equipment', icon: '🔬' },
  { id: 'Books & Notes', label: 'Books & Notes', icon: '📖' },
  { id: 'Cables & Adapters', label: 'Cables & Adapters', icon: '🔗' },
  { id: 'Stationery & Drawing', label: 'Stationery & Drawing', icon: '📐' },
  { id: 'Other', label: 'Other Items', icon: '📦' }
];

export default function TopActionBar({
  search,
  setSearch,
  category,
  setCategory,
  listingType,
  setListingType,
  onOpenAddModal,
  onToggleSidebar,
  totalItems = null
}) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showNotifications, setShowNotifications] = useState(false);

  // Notifications query
  const { data: notifications = [] } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => api.get('/notifications').then((res) => res.data),
    enabled: !!user,
    refetchInterval: 5000,
  });

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const markReadMutation = useMutation({
    mutationFn: (id) => api.put(`/notifications/${id}/read`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => api.put('/notifications/read-all'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  return (
    <header className="h-16 bg-white/95 backdrop-blur-md border-b border-slate-200 px-4 lg:px-6 flex items-center justify-between gap-3 z-20 flex-shrink-0">
      {/* Mobile Sidebar Toggle Button */}
      <button
        onClick={onToggleSidebar}
        className="lg:hidden p-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-800 transition-colors"
        title="Toggle Menu"
      >
        <MenuIcon />
      </button>

      {/* Search Input */}
      <div className="relative flex-1 max-w-xs md:max-w-md">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <SearchIcon />
        </div>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search calculators, chargers, books, roll..."
          className="w-full pl-9 pr-8 py-2 text-sm bg-slate-50 hover:bg-slate-100/80 focus:bg-white border border-slate-200 focus:border-blue-500 rounded-lg outline-none focus:ring-2 focus:ring-blue-500/20 text-slate-800 placeholder-slate-400 transition-all"
        />
        {search && (
          <button
            onClick={() => setSearch('')}
            className="absolute inset-y-0 right-0 pr-2.5 flex items-center"
            title="Clear search"
          >
            <CloseIcon />
          </button>
        )}
      </div>

      {/* Segmented Type Filter */}
      <div className="hidden sm:flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200/80 text-xs font-semibold">
        <button
          onClick={() => setListingType('ALL')}
          className={`px-3 py-1.5 rounded-md transition-all ${
            listingType === 'ALL'
              ? 'bg-white text-slate-900 shadow-xs'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          All Items
        </button>
        <button
          onClick={() => setListingType('lend')}
          className={`px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5 ${
            listingType === 'lend'
              ? 'bg-emerald-50 text-emerald-700 shadow-xs border border-emerald-200/80 font-bold'
              : 'text-slate-600 hover:text-emerald-700'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          Lending
        </button>
        <button
          onClick={() => setListingType('borrow')}
          className={`px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5 ${
            listingType === 'borrow'
              ? 'bg-rose-50 text-rose-700 shadow-xs border border-rose-200/80 font-bold'
              : 'text-slate-600 hover:text-rose-700'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
          Beacons
        </button>
      </div>

      {/* Category Dropdown */}
      <div className="hidden md:block">
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg px-3 py-2 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 cursor-pointer shadow-xs"
        >
          {CATEGORIES.map((cat) => (
            <option key={cat.id} value={cat.id}>
              {cat.icon} {cat.label}
            </option>
          ))}
        </select>
      </div>

      {/* Right Actions: Messages, Notifications, Add Item */}
      <div className="flex items-center gap-2 relative">
        {user && (
          <>
            {/* Direct Chat Link */}
            <button
              onClick={() => navigate('/chat')}
              className="p-2 text-slate-600 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition-colors relative"
              title="1:1 Messages"
            >
              <span className="text-lg">💬</span>
            </button>

            {/* Notification Bell */}
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="p-2 text-slate-600 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition-colors relative"
                title="Notifications"
              >
                <span className="text-lg">🔔</span>
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 w-4 h-4 bg-rose-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </button>

              {/* Notification Dropdown */}
              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 bg-white rounded-2xl shadow-xl border border-slate-200 py-2 z-50 overflow-hidden">
                  <div className="px-4 py-2 border-b border-slate-100 flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                      Notifications
                    </span>
                    {unreadCount > 0 && (
                      <button
                        onClick={() => markAllReadMutation.mutate()}
                        className="text-[11px] text-blue-600 hover:underline font-medium"
                      >
                        Mark all read
                      </button>
                    )}
                  </div>

                  <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
                    {notifications.length === 0 ? (
                      <p className="text-xs text-slate-400 p-4 text-center">No notifications yet.</p>
                    ) : (
                      notifications.map((n) => (
                        <div
                          key={n.id}
                          onClick={() => {
                            if (!n.is_read) markReadMutation.mutate(n.id);
                            if (n.link) {
                              setShowNotifications(false);
                              navigate(n.link);
                            }
                          }}
                          className={`p-3 text-xs cursor-pointer hover:bg-slate-50 transition ${
                            n.is_read ? 'opacity-70' : 'bg-blue-50/40 font-medium'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <p className="font-semibold text-slate-800">{n.title}</p>
                            <span className="text-[10px] text-slate-400">
                              {new Date(n.created_at).toLocaleTimeString([], {
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </span>
                          </div>
                          <p className="text-slate-600 mt-0.5 line-clamp-2">{n.message}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        <button
          id="btn-add-item-top"
          onClick={onOpenAddModal}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-semibold bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white shadow-sm hover:shadow transition-all"
        >
          <PlusIcon />
          <span className="hidden xs:inline">Add Item</span>
        </button>
      </div>
    </header>
  );
}
