import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import api, { API_ORIGIN } from '../api/client';
import Loader from '../components/common/Loader';
import RequestModal from '../components/requests/RequestModal';
import { useAuth } from '../context/AuthContext';

export default function ItemDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [showRequestModal, setShowRequestModal] = useState(false);

  const { data: item, isLoading, error } = useQuery({
    queryKey: ['item', id],
    queryFn: () => api.get(`/items/${id}`).then(res => res.data)
  });

  if (isLoading) return <Loader />;
  if (error) return <div className="text-red-500">Failed to load item</div>;

  const placeholderImage = 'https://via.placeholder.com/600x400?text=No+Image';
  const imageSrc = item.image_url ? `${API_ORIGIN}${item.image_url}` : placeholderImage;

  return (
    <div className="max-w-3xl mx-auto p-6">
      <img src={imageSrc} alt={item.title} className="w-full h-80 object-cover rounded-lg" />
      <h1 className="text-3xl font-bold mt-4">{item.title}</h1>
      <p className="text-gray-600 mt-2">{item.category} · {item.zone || 'Anywhere'}</p>
      <p className="mt-4">{item.description || 'No description provided.'}</p>
      <div className="mt-4 flex items-center gap-4">
        <span className="text-sm bg-green-100 text-green-800 px-3 py-1 rounded-full">
          {item.is_available ? 'Available' : 'Not Available'}
        </span>
        <span className="text-sm">⭐ {item.owner?.trust_score?.toFixed(1) || 4.5}</span>
      </div>
      <div className="mt-6 border-t pt-4">
        <p className="font-semibold">Owner: {item.owner?.name} ({item.owner?.dept})</p>
        <p className="text-sm text-gray-500">Roll: {item.owner?.roll}</p>
      </div>
      {user && item.is_available && user.id !== item.owner_id && (
        <button
          onClick={() => setShowRequestModal(true)}
          className="mt-6 w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700"
        >
          Request to Borrow
        </button>
      )}
      {showRequestModal && (
        <RequestModal itemId={item.id} onClose={() => setShowRequestModal(false)} />
      )}
    </div>
  );
}