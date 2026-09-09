import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { QRCodeSVG } from 'qrcode.react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

export default function Transaction() {
  const { requestId } = useParams();
  const { user } = useAuth();
  const [otp, setOtp] = useState('');
  const [qrData, setQrData] = useState(null);
  const [karmaResult, setKarmaResult] = useState(null);

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
            `🎉 Return complete! Borrower: +${karmaInfo.borrower_change} Karma, Lender: +${karmaInfo.owner_gain} Karma! ⚡`,
            { duration: 5000 }
          );
        } else {
          toast.error(
            `⚠️ Late return! Borrower penalized ${karmaInfo.borrower_change} Karma. Lender: +${karmaInfo.owner_gain} Karma.`,
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

  // Check if user is owner to start handover
  const isOwner = request && user && request.owner_id === user.id;

  return (
    <div className="max-w-xl mx-auto p-6 space-y-6 h-full overflow-y-auto">
      <h1 className="text-2xl font-bold text-slate-900">Exchange & Handover</h1>

      {request && (
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900">{request.item?.title}</h2>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 capitalize">
              {request.status}
            </span>
          </div>

          <div className="text-xs text-slate-600 space-y-1">
            <p><strong>Owner:</strong> {request.owner?.name || 'KUET Student'} ({request.owner?.dept})</p>
            <p><strong>Borrower:</strong> {request.borrower?.name || 'KUET Student'} ({request.borrower?.dept})</p>
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
            <span>{karmaResult.is_on_time ? '🎉 On-Time Exchange Completed!' : '⚠️ Late Return Processed'}</span>
          </div>
          <p className="text-xs mb-3">
            {karmaResult.is_on_time
              ? 'Both students demonstrated reliable campus citizenship under the KUET Karma Protocol.'
              : 'Return deadline was exceeded. Karma points adjusted accordingly.'}
          </p>
          <div className="grid grid-cols-2 gap-3 text-center text-xs">
            <div className="bg-white/80 p-2.5 rounded-xl border border-emerald-100 shadow-2xs">
              <span className="text-slate-500 block text-[10px]">Lender Award</span>
              <span className="font-bold text-emerald-700 text-sm">+{karmaResult.owner_gain} Karma ⚡</span>
            </div>
            <div className="bg-white/80 p-2.5 rounded-xl border border-emerald-100 shadow-2xs">
              <span className="text-slate-500 block text-[10px]">Borrower Change</span>
              <span className={`font-bold text-sm ${karmaResult.borrower_change >= 0 ? 'text-blue-700' : 'text-rose-700'}`}>
                {karmaResult.borrower_change >= 0 ? `+${karmaResult.borrower_change}` : karmaResult.borrower_change} Karma ⚡
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
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2.5 rounded-xl shadow-xs transition text-sm"
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
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 rounded-xl shadow-xs transition text-sm"
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
            className="w-full bg-amber-600 hover:bg-amber-700 text-white font-semibold py-2.5 rounded-xl shadow-xs transition text-sm"
            disabled={returnMutation.isPending}
          >
            {returnMutation.isPending ? 'Processing...' : 'Confirm Return & Update Karma ⚡'}
          </button>
        </div>
      )}
    </div>
  );
}
