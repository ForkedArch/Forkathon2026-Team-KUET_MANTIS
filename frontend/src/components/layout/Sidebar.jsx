import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

// Clean inline SVGs for zero-dependency portability
const MapIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
  </svg>
);

const PackageIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
  </svg>
);

const InboxIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 4H6a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-2m-4-1v8m0 0l3-3m-3 3L9 8m-5 5h2.586a1 1 0 01.707.293l2.414 2.414a1 1 0 00.707.293h3.172a1 1 0 00.707-.293l2.414-2.414a1 1 0 01.707-.293H20" />
  </svg>
);

const UserIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
);

const LogoutIcon = () => (
  <svg className="w-4 h-4 text-slate-400 hover:text-rose-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
  </svg>
);

export default function Sidebar({ isOpen, onClose }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navLinkClasses = ({ isActive }) =>
    `flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-blue-50 text-blue-700 font-semibold border border-blue-100 shadow-xs'
        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
    }`;

  // Helper to extract student initials
  const getInitials = (name) => {
    if (!name) return 'KU';
    const parts = name.trim().split(' ');
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-30 lg:hidden"
        />
      )}

      <aside
        className={`fixed lg:static top-0 bottom-0 left-0 w-64 bg-white border-r border-slate-200 flex flex-col z-40 transition-transform duration-200 ease-in-out flex-shrink-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Branding Header */}
        <div className="p-5 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white font-black text-xl flex items-center justify-center shadow-md shadow-blue-500/20">
              K
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-base tracking-tight text-slate-900">
                  CampusShare
                </span>
                <span className="text-[10px] font-bold bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded">
                  KUET
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium">Peer-to-Peer Campus Hub</p>
            </div>
          </div>

          {/* 700m Campus Perimeter Badge */}
          <div className="mt-3.5 flex items-center gap-2 px-2.5 py-1 rounded-full bg-blue-50/80 border border-blue-200/60 text-blue-700 text-xs font-semibold">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-600"></span>
            </span>
            <span>📍 700m Campus Perimeter</span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Navigation
          </div>

          <NavLink to="/" end className={navLinkClasses} onClick={onClose}>
            <div className="flex items-center gap-3">
              <MapIcon />
              <span>Map View</span>
            </div>
            <span className="text-[11px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
              God's Eye
            </span>
          </NavLink>

          <NavLink to="/items" className={navLinkClasses} onClick={onClose}>
            <div className="flex items-center gap-3">
              <PackageIcon />
              <span>All Items</span>
            </div>
            <span className="text-[11px] font-semibold text-slate-400">Browse</span>
          </NavLink>

          <NavLink to="/requests" className={navLinkClasses} onClick={onClose}>
            <div className="flex items-center gap-3">
              <InboxIcon />
              <span>Borrow Requests</span>
            </div>
          </NavLink>

          <NavLink to="/profile" className={navLinkClasses} onClick={onClose}>
            <div className="flex items-center gap-3">
              <UserIcon />
              <span>My Profile</span>
            </div>
            <span className="text-[11px] font-bold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200/60">
              Karma
            </span>
          </NavLink>
        </nav>

        {/* Active Student Footer Card */}
        <div className="p-3 border-t border-slate-200 bg-slate-50/60">
          {user ? (
            <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-indigo-600 text-white font-bold text-xs flex items-center justify-center flex-shrink-0 shadow-xs">
                    {getInitials(user.name)}
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-bold text-slate-900 truncate" title={user.name}>
                      {user.name}
                    </p>
                    <p className="text-[11px] text-slate-500 truncate">
                      Roll: {user.roll || 'KUET'} · {user.dept || 'Stud'}
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleLogout}
                  className="p-1 rounded hover:bg-rose-50 transition-colors"
                  title="Logout"
                >
                  <LogoutIcon />
                </button>
              </div>

              {/* Karma Score Badge (R4) */}
              <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-500 font-medium">KUET Karma</span>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200 shadow-xs">
                  <span>⚡</span>
                  <span>{user.karma ?? 100} Karma</span>
                </span>
              </div>
            </div>
          ) : (
            <div className="bg-white p-3 rounded-xl border border-dashed border-slate-300 text-center">
              <p className="text-xs font-bold text-slate-800">KUET Student Portal</p>
              <p className="text-[11px] text-slate-500 mt-0.5 mb-2">
                Sign in with @stud.kuet.ac.bd
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => navigate('/login')}
                  className="flex-1 py-1.5 text-xs font-semibold bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Log In
                </button>
                <button
                  onClick={() => navigate('/register')}
                  className="flex-1 py-1.5 text-xs font-semibold bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
                >
                  Register
                </button>
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
