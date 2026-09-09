import { useState } from 'react';
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
      toast.success('Handover started! Share OTP or QR.');
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed')
  });

  const verifyMutation = useMutation({
    mutationFn: (otp) => api.post('/transactions/verify', { request_id: requestId, otp }),
    onSuccess: () => {
      toast.success('Handover verified! Item borrowed.');
      refetch();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Invalid OTP')
  });

  const returnMutation = useMutation({
    mutationFn: () => api.post(`/transactions/return/${requestId}`),
    onSuccess: () => {
      toast.success('Return confirmed!');
      refetch();
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed')
  });

  // Check if user is owner to start handover
  const isOwner = request && user && request.owner_id === user.id;

  return (
    <div className="max-w-md mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Handover</h1>
      {request && (
        <div className="border rounded p-4 mb-4">
          <p><strong>Item:</strong> {request.item.title}</p>
          <p><strong>Status:</strong> {request.status}</p>
          {request.transaction && (
            <p><strong>Transaction Status:</strong> {request.transaction.status}</p>
          )}
        </div>
      )}
      {isOwner && (!qrData) && (
        <button
          onClick={() => startMutation.mutate()}
          className="bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
          disabled={startMutation.isPending}
        >
          {startMutation.isPending ? 'Starting...' : 'Start Handover'}
        </button>
      )}
      {qrData && (
        <div className="mt-4">
          <p className="font-semibold">OTP: {qrData.otp}</p>
          <QRCodeSVG value={`${requestId}:${qrData.otp}`} size={200} />
          <p className="text-sm text-gray-500 mt-2">Share this QR or OTP with borrower</p>
        </div>
      )}
      {!isOwner && request?.status === 'accepted' && (
        <div className="mt-4">
          <p className="font-semibold">Enter OTP from owner</p>
          <input
            type="text"
            className="border rounded px-3 py-2 w-full"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            placeholder="OTP"
          />
          <button
            onClick={() => verifyMutation.mutate(otp)}
            className="mt-2 bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700"
            disabled={verifyMutation.isPending}
          >
            {verifyMutation.isPending ? 'Verifying...' : 'Verify Handover'}
          </button>
        </div>
      )}
      {request?.transaction?.status === 'borrowed' && request.borrower_id === user.id && (
        <button
          onClick={() => returnMutation.mutate()}
          className="mt-4 bg-yellow-600 text-white py-2 px-4 rounded hover:bg-yellow-700"
        >
          Request Return
        </button>
      )}
    </div>
  );
}