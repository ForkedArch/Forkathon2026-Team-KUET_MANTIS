import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { QRCodeSVG } from 'qrcode.react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { formatDept } from '../utils/dept';
import { KarmaIcon } from '../components/common/KarmaIcon';
import toast from 'react-hot-toast';

export default function Transaction() {
  const { requestId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [otp, setOtp] = useState('');
  const [qrData, setQrData] = useState(null);
  const [karmaResult, setKarmaResult] = useState(null);

  // Review form state
  const [rating, setRating] = useState(5);
  const [reviewComment, setReviewComment] = useState('');
  const [reviewSubmitted, setReviewSubmitted] = useState(false);

  // Fetch transaction details if exists
  const { data: request, refetch } = useQuery({
    queryKey: ['request', requestId],
    queryFn: () => api.get(`/requests/me`).then(res => {
      const found = res.data.find(r => r.id === parseInt(requestId));
      return found;
    }),
    enabled: !!requestId
  });

  const startMutation = useMutation({
    mutationFn: () => api.post('/transactions/start', { request_id: requestId }),
    onSuccess: (res) => {
      setQrData(res.data);
      toast.success('Handover started! Share OTP or QR with borrower.');
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed to start handover')
  });

  const verifyMutation = useMutation({
    mutationFn: (enteredOtp) => api.post('/transactions/verify', { request_id: requestId, otp: enteredOtp }),
    onSuccess: () => {
      toast.success('Handover verified! Item status updated to borrowed.');
      refetch();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Invalid OTP')
  });

  const returnMutation = useMutation({
    mutationFn: () => api.post(`/transactions/return/${requestId}`),
    onSuccess: (res) => {
      const karmaInfo = res.data?.karma_updated;
      if (karmaInfo) {
        setKarmaResult(karmaInfo);
        if (karmaInfo.is_on_time) {
          toast.success(
            `Return complete! Borrower: +${karmaInfo.borrower_change} Karma, Lender: +${karmaInfo.owner_gain} Karma!`,
            { duration: 5000 }
          );
        } else {
          toast.error(
            `Late return! Borrower penalized ${karmaInfo.borrower_change} Karma. Lender: +${karmaInfo.owner_gain} Karma.`,
            { duration: 5000 }
          );
        }
      } else {
        toast.success('Return confirmed! KUET Karma scores updated.');
      }
      refetch();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed to process return')
  });

  const reviewMutation = useMutation({
    mutationFn: (data) => api.post('/reviews', data),
    onSuccess: () => {
      toast.success('Thank you for rating your fellow KUETian!');
      setReviewSubmitted(true);
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed to submit review')
  });

  // Check if user is owner to start handover
  const isOwner = request && user && request.owner_id === user.id;
  const counterpart = isOwner ? request?.borrower : request?.owner;

  const handleReviewSubmit = (e) => {
    e.preventDefault();
    if (!counterpart?.id) return;
    reviewMutation.mutate({
      transaction_id: request?.transaction?.id,
      reviewee_id: counterpart.id,
      rating,
      comment: reviewComment.trim()
    });
  };

  return (
    <div className="max-w-xl mx-auto p-6 space-y-6 h-full overflow-y-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Exchange & Handover</h1>
        {counterpart && (
          <button
            onClick={() => navigate(`/chat?user=${counterpart.id}`)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-xl text-xs font-semibold transition"
          >
            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <span>Chat with {isOwner ? 'Borrower' : 'Owner'}</span>
          </button>
        )}
      </div>

      {request && (
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900">{request.item?.title}</h2>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 capitalize">
              {request.status}
            </span>
          </div>

          <div className="text-xs text-slate-600 space-y-1">
            <p><strong>Owner:</strong> {request.owner?.name || 'KUET Student'} ({formatDept(request.owner?.dept)})</p>
            <p><strong>Borrower:</strong> {request.borrower?.name || 'KUET Student'} ({formatDept(request.borrower?.dept)})</p>
            <p><strong>Duration:</strong> {request.duration_hours} hours</p>
            {request.transaction && (
              <p><strong>Transaction Status:</strong> <span className="font-semibold text-emerald-600 capitalize">{request.transaction.status}</span></p>
            )}
          </div>
        </div>
      )}

      {/* Karma Celebration Feedback Card */}
      {karmaResult && (
        <div className={`p-4 rounded-2xl border shadow-sm ${karmaResult.is_on_time ? 'bg-emerald-50 border-emerald-200 text-emerald-950' : 'bg-amber-50 border-amber-200 text-amber-950'}`}>
          <div className="flex items-center gap-2 font-bold text-sm mb-1">
            {karmaResult.is_on_time ? (
              <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ) : (
              <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            )}
            <span>{karmaResult.is_on_time ? 'On-Time Exchange Completed!' : 'Late Return Processed'}</span>
          </div>
          <p className="text-xs mb-3">
            {karmaResult.is_on_time
              ? 'Both students demonstrated reliable campus citizenship under the KUET Karma Protocol.'
              : 'Return deadline was exceeded. Karma points adjusted accordingly.'}
          </p>
          <div className="grid grid-cols-2 gap-3 text-center text-xs">
            <div className="bg-white/80 p-2.5 rounded-xl border border-emerald-100 shadow-2xs">
              <span className="text-slate-500 block text-[10px]">Lender Award</span>
              <span className="font-bold text-emerald-700 text-sm flex items-center justify-center gap-1 mt-0.5">
                <span>+{karmaResult.owner_gain} Karma</span>
                <KarmaIcon className="w-3.5 h-3.5 text-emerald-600" />
              </span>
            </div>
            <div className="bg-white/80 p-2.5 rounded-xl border border-emerald-100 shadow-2xs">
              <span className="text-slate-500 block text-[10px]">Borrower Change</span>
              <span className={`font-bold text-sm flex items-center justify-center gap-1 mt-0.5 ${karmaResult.borrower_change >= 0 ? 'text-blue-700' : 'text-rose-700'}`}>
                <span>{karmaResult.borrower_change >= 0 ? `+${karmaResult.borrower_change}` : karmaResult.borrower_change} Karma</span>
                <KarmaIcon className="w-3.5 h-3.5 text-amber-500" />
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Handover Start (Owner) */}
      {isOwner && (!qrData) && request?.status === 'accepted' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs text-center space-y-3">
          <p className="text-sm font-semibold text-slate-800">Ready for Physical Handover?</p>
          <p className="text-xs text-slate-500">Generate a one-time OTP and QR code to share with the borrower on campus.</p>
          <button
            onClick={() => startMutation.mutate()}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 rounded-xl shadow-xs transition text-sm cursor-pointer"
            disabled={startMutation.isPending}
          >
            {startMutation.isPending ? 'Starting...' : 'Start Handover & Generate OTP'}
          </button>
        </div>
      )}

      {/* QR & OTP Display */}
      {qrData && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs text-center space-y-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block mb-1">Handover Verification OTP</span>
            <div className="text-3xl font-mono font-extrabold text-blue-600 tracking-widest">{qrData.otp}</div>
          </div>

          <div className="flex justify-center p-3 bg-slate-50 rounded-xl border border-slate-100 inline-block mx-auto">
            <QRCodeSVG value={`${requestId}:${qrData.otp}`} size={180} />
          </div>
          <p className="text-xs text-slate-500">Show this QR code or 6-digit OTP to the borrower to verify physical handover.</p>
        </div>
      )}

      {/* Handover Verification (Borrower) */}
      {!isOwner && request?.status === 'accepted' && (!request.transaction || request.transaction.status !== 'borrowed') && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-3">
          <h3 className="text-sm font-bold text-slate-800">Verify Item Receipt</h3>
          <p className="text-xs text-slate-500">Enter the 6-digit handover OTP provided by the owner upon receiving the item.</p>
          <input
            type="text"
            className="w-full border border-slate-200 rounded-xl px-3.5 py-2.5 text-center font-mono text-lg tracking-widest outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            placeholder="000000"
            maxLength={6}
          />
          <button
            onClick={() => verifyMutation.mutate(otp)}
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 rounded-xl shadow-xs transition text-sm cursor-pointer"
            disabled={verifyMutation.isPending || !otp}
          >
            {verifyMutation.isPending ? 'Verifying...' : 'Verify Handover & Receive Item'}
          </button>
        </div>
      )}

      {/* Return Item Action (Borrower) */}
      {request?.transaction?.status === 'borrowed' && request.borrower_id === user?.id && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-3">
          <h3 className="text-sm font-bold text-slate-800">Return Item to Owner</h3>
          <p className="text-xs text-slate-500">
            Confirm you have physically handed the item back to the owner. Returning on-time awards <strong>+5 Karma</strong>!
          </p>
          <button
            onClick={() => returnMutation.mutate()}
            className="w-full bg-amber-600 hover:bg-amber-700 text-white font-semibold py-2.5 rounded-xl shadow-xs transition text-sm cursor-pointer flex items-center justify-center gap-1.5"
            disabled={returnMutation.isPending}
          >
            {returnMutation.isPending ? (
              'Processing...'
            ) : (
              <>
                <span>Confirm Return & Update Karma</span>
                <KarmaIcon className="w-4 h-4 text-white" />
              </>
            )}
          </button>
        </div>
      )}

      {/* Peer Review & Rating Section */}
      {(request?.status === 'completed' || request?.transaction?.status === 'returned') && counterpart && (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-800">Rate Your Experience with {counterpart?.name}</h3>
            <span className="text-xs bg-amber-50 text-amber-700 font-semibold px-2 py-0.5 rounded-md">Verified Review</span>
          </div>

          {reviewSubmitted ? (
            <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs text-center font-medium flex items-center justify-center gap-2">
              <svg className="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
              </svg>
              <span>Your review has been recorded on {counterpart?.name}'s campus profile. Thank you!</span>
            </div>
          ) : (
            <form onSubmit={handleReviewSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1.5">Rating (1 to 5 Stars)</label>
                <div className="flex items-center gap-1.5">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setRating(star)}
                      className="p-1 transition hover:scale-110 focus:outline-none cursor-pointer"
                    >
                      <svg
                        className={`w-6 h-6 ${star <= rating ? 'text-amber-400 fill-amber-400' : 'text-slate-300 stroke-slate-300'}`}
                        fill={star <= rating ? 'currentColor' : 'none'}
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                      </svg>
                    </button>
                  ))}
                  <span className="text-xs font-bold text-amber-600 ml-2">{rating} / 5 Stars</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Feedback / Comment (Optional)</label>
                <textarea
                  className="w-full border border-slate-200 rounded-xl p-3 text-xs focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none resize-none"
                  rows={2}
                  placeholder={`Share how the transaction went with ${counterpart?.name}...`}
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value)}
                />
              </div>

              <button
                type="submit"
                disabled={reviewMutation.isPending}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 rounded-xl text-xs shadow-xs transition cursor-pointer"
              >
                {reviewMutation.isPending ? 'Submitting Review...' : 'Submit Rating & Feedback ⭐'}
              </button>
            </form>
          )}
        </div>
      )}
    </div>
  );
}

