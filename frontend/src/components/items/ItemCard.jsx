import { Link, useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api, { API_ORIGIN } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import toast from 'react-hot-toast';

export default function ItemCard({ item }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const placeholderImage = 'https://via.placeholder.com/300x200?text=CampusShare+KUET';

  const saveMutation = useMutation({
    mutationFn: () => api.post(`/items/${item.id}/save`),
    onSuccess: (res) => {
      toast.success(res.data.message);
      queryClient.invalidateQueries({ queryKey: ['saved-items'] });
      queryClient.invalidateQueries({ queryKey: ['items'] });
    },
    onError: () => toast.error('Please login to save items'),
  });

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden hover:shadow-md transition flex flex-col group relative">
      <div className="relative h-48 bg-slate-100 overflow-hidden">
        <img
          src={item.image_url ? `${API_ORIGIN}${item.image_url}` : placeholderImage}
          alt={item.title}
          className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
          onError={(e) => (e.target.src = placeholderImage)}
        />
        {user && (
          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              saveMutation.mutate();
            }}
            className="absolute top-3 right-3 bg-white/90 backdrop-blur p-1.5 rounded-full shadow-sm hover:bg-white text-rose-600 transition"
            title="Bookmark Item"
          >
            <span className="text-sm">❤️</span>
          </button>
        )}
      </div>

      <div className="p-4 flex-1 flex flex-col justify-between">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
            {item.category}
          </span>
          <h3 className="font-bold text-base text-slate-900 truncate mt-1.5" title={item.title}>
            {item.title}
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">📍 {item.zone || 'Campus Center'}</p>
        </div>

        <div className="mt-3">
          <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-100">
            <span
              className={`font-semibold ${
                item.type === 'borrow'
                  ? 'text-rose-600'
                  : item.is_available
                  ? 'text-emerald-600'
                  : 'text-slate-400'
              }`}
            >
              {item.type === 'borrow' ? '🚨 Borrow Beacon' : item.is_available ? '🟢 Available' : '🔒 Borrowed'}
            </span>
            <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-900 border border-amber-200">
              ⚡ {item.owner?.karma ?? item.karma ?? 100}
            </span>
          </div>

          <div className="mt-3 flex gap-2">
            <Link
              to={`/item/${item.id}`}
              className="flex-1 text-center bg-blue-600 text-white py-2 rounded-xl text-xs font-semibold hover:bg-blue-700 transition"
            >
              View
            </Link>
            {user && user.id !== item.owner_id && (
              <button
                onClick={() => navigate(`/chat?user=${item.owner_id}&item=${item.id}`)}
                className="px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
                title="Direct Chat with Owner"
              >
                💬
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
