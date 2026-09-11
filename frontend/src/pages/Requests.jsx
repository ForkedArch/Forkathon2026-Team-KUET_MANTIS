import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import api from '../api/client';
import Loader from '../components/common/Loader';
import { useAuth } from '../context/AuthContext';
import { formatDept } from '../utils/dept';
import { KarmaIcon } from '../components/common/KarmaIcon';
import toast from 'react-hot-toast';

const ClockIcon = ({ className = "w-3.5 h-3.5" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const MapPinIcon = ({ className = "w-3.5 h-3.5" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

const TargetIcon = ({ className = "w-3.5 h-3.5" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
  </svg>
);

const HandoverIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
  </svg>
);

const ChatBubbleIcon = ({ className = "w-3.5 h-3.5" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
  </svg>
);

const InboxEmptyIcon = ({ className = "w-6 h-6" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
  </svg>
);

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
          <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-3 shadow-2xs">
            <InboxEmptyIcon className="w-6 h-6" />
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
                        <span className="inline-flex items-center gap-1.5 text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-900 border border-amber-200 shadow-2xs">
                          <KarmaIcon className="w-3 h-3 text-amber-500" />
                          <span>{karmaScore} Karma</span>
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-slate-600">
                      {isMyRequest
                        ? `You requested from ${req.owner?.name || 'KUET Student'} (${formatDept(req.owner?.dept)} • Roll ${req.owner?.roll || 'KUET'})`
                        : `Request from ${req.borrower?.name || 'KUET Student'} (${formatDept(req.borrower?.dept)} • Roll ${req.borrower?.roll || 'KUET'})`}
                    </p>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 pt-1">
                      <span className="flex items-center gap-1.5">
                        <ClockIcon className="w-3.5 h-3.5 text-slate-400" />
                        <span><strong>Duration:</strong> {req.duration_hours}h</span>
                      </span>
                      <span>·</span>
                      <span className="flex items-center gap-1.5">
                        <MapPinIcon className="w-3.5 h-3.5 text-slate-400" />
                        <span><strong>Pickup:</strong> {req.pickup_zone || 'Campus'}</span>
                      </span>
                      {req.purpose && (
                        <>
                          <span>·</span>
                          <span className="flex items-center gap-1.5">
                            <TargetIcon className="w-3.5 h-3.5 text-slate-400" />
                            <span><strong>Purpose:</strong> {req.purpose}</span>
                          </span>
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

                {/* Chat Link — available immediately after request, for any status */}
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  {req.status === 'accepted' ? (
                    <Link
                      to={`/transaction/${req.id}`}
                      className="font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1.5"
                    >
                      <HandoverIcon className="w-4 h-4" />
                      <span>Go to Handover &amp; OTP Verification</span>
                    </Link>
                  ) : (
                    <span className="text-slate-400 italic text-[11px]">
                      {req.status === 'pending' ? 'Awaiting response — coordinate via chat below' : `Request ${req.status}`}
                    </span>
                  )}
                  <Link
                    to={`/chat?user=${otherParty?.id}&item=${req.item?.id}`}
                    className="text-slate-600 hover:text-blue-700 bg-slate-100 hover:bg-blue-50 hover:border-blue-200 border border-transparent px-3 py-1.5 rounded-lg font-semibold transition flex items-center gap-1.5"
                  >
                    <ChatBubbleIcon className="w-3.5 h-3.5" />
                    <span>Message {otherParty?.name?.split(' ')[0] || 'them'}</span>
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
