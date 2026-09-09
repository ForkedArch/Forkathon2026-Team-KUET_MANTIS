import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import Loader from '../components/common/Loader';
import { useAuth } from '../context/AuthContext';
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
      toast.success(`Request ${status}`);
      refetch();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed');
    }
  };

  if (isLoading) return <Loader />;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">My Requests</h1>
      {requests?.length === 0 ? (
        <p>No requests found.</p>
      ) : (
        <div className="space-y-4">
          {requests?.map(req => (
            <div key={req.id} className="border rounded-lg p-4 shadow-sm">
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-semibold">{req.item.title}</p>
                  <p className="text-sm text-gray-600">
                    {req.borrower_id === user.id ? 'You requested' : `Request from ${req.borrower.name}`}
                  </p>
                  <p className="text-sm">Duration: {req.duration_hours}h</p>
                  <p className="text-sm">Status: <span className="font-medium capitalize">{req.status}</span></p>
                </div>
                {req.owner_id === user.id && req.status === 'pending' && (
                  <div className="space-x-2">
                    <button
                      onClick={() => handleStatusUpdate(req.id, 'accepted')}
                      className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700"
                    >
                      Accept
                    </button>
                    <button
                      onClick={() => handleStatusUpdate(req.id, 'declined')}
                      className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                    >
                      Decline
                    </button>
                  </div>
                )}
              </div>
              {req.status === 'accepted' && (
                <div className="mt-2">
                  <a
                    href={`/chat/${req.id}`}
                    className="text-blue-600 hover:underline"
                  >
                    Open Chat
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}