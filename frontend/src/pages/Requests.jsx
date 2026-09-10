import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import api from '../api/client';
import Loader from '../components/common/Loader';
import { useAuth } from '../context/AuthContext';
import { formatDept } from '../utils/dept';
import toast from 'react-hot-toast';

export default function Requests() {
  const { user } = useAuth();

  const { data: requests, isLoading, refetch } = useQuery({
    queryKey: ['requests'],
    queryFn: () => api.get('/requests/me').then(res => res.data),
    enabled: !!user
  });

  const handleStatusUpdate = async (requestId, status) => {
    try {
      await api.put(`/requests/${requestId}/status?status=${status}`);
      toast.success(`Request marked as ${status}`);
      refetch();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update request status');
    }
  };

  if (isLoading) return <Loader />;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6 h-full overflow-y-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Borrow Requests</h1>
          <p className="text-xs text-slate-500">Incoming requests and your active borrow transactions</p>
        </div>
        <span className="text-xs font-semibold bg-white border border-slate-200 px-3 py-1.5 rounded-lg shadow-xs text-slate-600">
          {requests?.length || 0} Total
        </span>
      </div>

      {requests?.length === 0 ? (
        <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center max-w-md mx-auto shadow-xs">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3 text-2xl">
            📬
          </div>
          <h3 className="font-bold text-slate-800 text-base mb-1">No Active Requests</h3>
          <p className="text-xs text-slate-500">
            Browse the campus God's Eye map to find supplies or broadcast your own item!
          </p>
        </div>
      ) : (
        <div className="space-y-4 pb-12">
          {requests?.map(req => {
            const isMyRequest = req.borrower_id === user?.id;
            const otherParty = isMyRequest ? req.owner : req.borrower;
            const karmaScore = otherParty?.karma ?? 100;

            return (
              <div key={req.id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3 hover:border-slate-300 transition-colors">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-slate-900 text-base">{req.item?.title}</h3>
                      {otherParty && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-900 border border-amber-200 shadow-2xs">
                          ⚡ {karmaScore} Karma
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-slate-600">
                      {isMyRequest
                        ? `You requested from ${req.owner?.name || 'KUET Student'} (${formatDept(req.owner?.dept)} • Roll ${req.owner?.roll || 'KUET'})`
                        : `Request from ${req.borrower?.name || 'KUET Student'} (${formatDept(req.borrower?.dept)} • Roll ${req.borrower?.roll || 'KUET'})`}
                    </p>

                    <div className="flex flex-wrap gap-2 text-xs text-slate-500 pt-1">
                      <span>⏱️ <strong>Duration:</strong> {req.duration_hours}h</span>
                      <span>·</span>
                      <span>📍 <strong>Pickup:</strong> {req.pickup_zone || 'Campus'}</span>
                      {req.purpose && (
                        <>
                          <span>·</span>
                          <span>🎯 <strong>Purpose:</strong> {req.purpose}</span>
                        </>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-bold px-2.5 py-1 rounded-full uppercase tracking-wider ${
                      req.status === 'accepted'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : req.status === 'declined'
                        ? 'bg-rose-50 text-rose-700 border border-rose-200'
                        : 'bg-amber-50 text-amber-700 border border-amber-200'
                    }`}>
                      {req.status}
                    </span>

                    {/* Owner Action Buttons */}
                    {!isMyRequest && req.status === 'pending' && (
                      <div className="flex gap-1.5 ml-2">
                        <button
                          onClick={() => handleStatusUpdate(req.id, 'accepted')}
                          className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-2xs transition"
                        >
                          Accept
                        </button>
                        <button
                          onClick={() => handleStatusUpdate(req.id, 'declined')}
                          className="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-xs font-semibold transition"
                        >
                          Decline
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Handover & Chat Links */}
                {req.status === 'accepted' && (
                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <Link
                      to={`/transaction/${req.id}`}
                      className="font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
                    >
                      <span>🔄 Go to Handover & OTP Verification</span>
                    </Link>
                    <Link
                      to={`/chat/${req.id}`}
                      className="text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg font-medium transition"
                    >
                      💬 Open Chat
                    </Link>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
