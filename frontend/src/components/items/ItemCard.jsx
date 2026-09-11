import { Link, useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api, { API_ORIGIN } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { KarmaIcon } from '../common/KarmaIcon';
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
            className="absolute top-3 right-3 bg-white/90 backdrop-blur p-1.5 rounded-full shadow-sm hover:bg-white text-rose-500 hover:text-rose-600 transition"
            title="Bookmark Item"
          >
            <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
            </svg>
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
          <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
            <svg className="w-3.5 h-3.5 text-slate-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span className="truncate">{item.zone || 'Campus Center'}</span>
          </p>
        </div>

        <div className="mt-3">
          <div className="flex items-center justify-between text-xs pt-2.5 border-t border-slate-100">
            <span
              className={`inline-flex items-center gap-1.5 font-semibold text-xs ${
                item.type === 'borrow'
                  ? 'text-rose-600'
                  : item.is_available
                  ? 'text-emerald-600'
                  : 'text-slate-400'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  item.type === 'borrow'
                    ? 'bg-rose-500 animate-pulse'
                    : item.is_available
                    ? 'bg-emerald-500'
                    : 'bg-slate-400'
                }`}
              />
              {item.type === 'borrow' ? 'Borrow Beacon' : item.is_available ? 'Available' : 'Borrowed'}
            </span>
            <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-900 border border-amber-200">
              <KarmaIcon className="w-3 h-3 text-amber-500" />
              <span>{item.owner?.karma ?? item.karma ?? 100}</span>
            </span>
          </div>

          <div className="mt-3 flex gap-2">
            <Link
              to={`/item/${item.id}`}
              className="flex-1 text-center bg-blue-600 text-white py-2 rounded-xl text-xs font-semibold hover:bg-blue-700 transition shadow-xs"
            >
              View
            </Link>
            {user && user.id !== item.owner_id && (
              <button
                onClick={() => navigate(`/chat?user=${item.owner_id}&item=${item.id}`)}
                className="px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition flex items-center justify-center"
                title="Direct Chat with Owner"
              >
                <svg className="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
