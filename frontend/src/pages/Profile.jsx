import React from 'react';
import { useAuth } from '../context/AuthContext';

export default function Profile() {
  const { user } = useAuth();
  if (!user) return <div className="p-8 text-center text-slate-500">Please log in to view profile.</div>;

  const karma = user.karma ?? 100;
  const netKarmaChange = karma - 100;

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6 h-full overflow-y-auto">
      <h1 className="text-2xl font-bold text-slate-900">Student Profile & Karma Record</h1>

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
            Base Karma: 100 · Earn +10 per lend · +5 for on-time returns · -30 late penalty
          </p>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl p-3 text-center sm:text-right border border-white/20">
          <span className="text-[11px] text-amber-100 block">Exchanges Completed</span>
          <span className="text-2xl font-bold">{(user.total_lends || 0) + (user.total_borrows || 0)}</span>
          <span className="text-[10px] text-amber-200 block">({user.total_lends || 0} Lends, {user.total_borrows || 0} Borrows)</span>
        </div>
      </div>

      {/* Profile Details & Protocol Reference */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-12">
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
              <span className="font-semibold text-slate-900">{user.dept || 'CSE'}</span>
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
    </div>
  );
}
