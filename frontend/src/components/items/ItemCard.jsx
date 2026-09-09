import { Link } from 'react-router-dom';
import { API_ORIGIN } from '../../api/client';

export default function ItemCard({ item }) {
  const placeholderImage = 'https://via.placeholder.com/300x200?text=No+Image';
  return (
    <div className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-lg transition">
      <img
        src={item.image_url ? `${API_ORIGIN}${item.image_url}` : placeholderImage}
        alt={item.title}
        className="w-full h-48 object-cover"
        onError={(e) => e.target.src = placeholderImage}
      />
      <div className="p-4">
        <h3 className="font-bold text-lg truncate">{item.title}</h3>
        <p className="text-sm text-gray-600">{item.category} · {item.zone || 'Anywhere'}</p>
        <div className="flex items-center justify-between mt-2">
          <span className="text-sm text-green-600 font-semibold">Available</span>
          <span className="text-sm">⭐ {item.owner?.trust_score?.toFixed(1) || 4.5}</span>
        </div>
        <Link to={`/item/${item.id}`} className="mt-3 inline-block w-full text-center bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">
          View Details
        </Link>
      </div>
    </div>
  );
}