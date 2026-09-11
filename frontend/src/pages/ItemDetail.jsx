import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import api, { API_ORIGIN } from '../api/client';
import Loader from '../components/common/Loader';
import RequestModal from '../components/requests/RequestModal';
import { useAuth } from '../context/AuthContext';
import { formatDept } from '../utils/dept';
import { KarmaIcon } from '../components/common/KarmaIcon';
import toast from 'react-hot-toast';

export default function ItemDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const [showRequestModal, setShowRequestModal] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [reportReason, setReportReason] = useState('Inappropriate content');
  const [reportDetails, setReportDetails] = useState('');

  // Fetch Item
  const { data: item, isLoading, error } = useQuery({
    queryKey: ['item', id],
    queryFn: () => api.get(`/items/${id}`).then((res) => res.data),
  });

  // Edit Form State
  const [editForm, setEditForm] = useState(null);

  // Wishlist Save Mutation
  const saveMutation = useMutation({
    mutationFn: () => api.post(`/items/${id}/save`),
    onSuccess: (res) => {
      toast.success(res.data.message);
      queryClient.invalidateQueries({ queryKey: ['saved-items'] });
      queryClient.invalidateQueries({ queryKey: ['item', id] });
    },
    onError: () => toast.error('Failed to update wishlist'),
  });

  // Report Mutation
  const reportMutation = useMutation({
    mutationFn: (data) => api.post(`/items/${id}/report`, data),
    onSuccess: () => {
      toast.success('Report submitted to campus admins.');
      setShowReportModal(false);
      setReportDetails('');
    },
    onError: () => toast.error('Failed to submit report'),
  });

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: () => api.delete(`/items/${id}`),
    onSuccess: () => {
      toast.success('Listing deleted.');
      navigate('/items');
    },
    onError: () => toast.error('Failed to delete item'),
  });

  // Edit Mutation
  const editMutation = useMutation({
    mutationFn: (data) => api.put(`/items/${id}`, data),
    onSuccess: () => {
      toast.success('Listing updated.');
      setShowEditModal(false);
      queryClient.invalidateQueries({ queryKey: ['item', id] });
    },
    onError: () => toast.error('Failed to update item'),
  });

  if (isLoading) return <Loader />;
  if (error || !item) return <div className="text-red-500 p-6 text-center">Failed to load item</div>;

  const placeholderImage = 'https://via.placeholder.com/600x400?text=CampusShare+KUET';
  const imageSrc = item.image_url ? `${API_ORIGIN}${item.image_url}` : placeholderImage;
  const isOwner = user && user.id === item.owner_id;

  const handleOpenEdit = () => {
    setEditForm({
      title: item.title,
      description: item.description || '',
      category: item.category,
      specs: item.specs || '',
      condition: item.condition || 'Good',
      zone: item.zone || '',
      is_available: item.is_available,
    });
    setShowEditModal(true);
  };

  return (
    <div className="max-w-3xl mx-auto p-4 sm:p-6 pb-16">
      {/* Top Media & Header */}
      <div className="relative rounded-2xl overflow-hidden shadow-sm border border-slate-200">
        <img src={imageSrc} alt={item.title} className="w-full h-80 sm:h-96 object-cover bg-slate-100" />
        
        {/* Wishlist Button */}
        {user && (
          <button
            onClick={() => saveMutation.mutate()}
            className="absolute top-4 right-4 bg-white/90 backdrop-blur p-2.5 rounded-full shadow-md hover:bg-white text-rose-500 hover:text-rose-600 transition"
            title="Save to Wishlist"
          >
            <svg className="w-5 h-5 fill-current" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>

      {/* Main Info */}
      <div className="mt-6 flex items-start justify-between gap-4">
        <div>
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-md uppercase tracking-wider inline-flex items-center gap-1.5 ${
            item.type === 'lend' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/60' : 'bg-rose-50 text-rose-700 border border-rose-200/60'
          }`}>
            <span className={`w-2 h-2 rounded-full ${item.type === 'lend' ? 'bg-emerald-500' : 'bg-rose-500 animate-pulse'}`} />
            {item.type === 'lend' ? 'For Lend' : 'Needed (Borrow Beacon)'}
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 mt-2">{item.title}</h1>
          <p className="text-sm text-slate-500 mt-1 flex items-center gap-1.5">
            <span>{item.category}</span>
            <span>·</span>
            <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span>{item.zone || 'Anywhere on Campus'}</span>
          </p>
        </div>

        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <span
            className={`text-xs font-bold px-3 py-1 rounded-full ${
              item.is_available
                ? 'bg-emerald-100 text-emerald-800'
                : 'bg-slate-100 text-slate-600'
            }`}
          >
            {item.is_available ? 'Available' : 'Currently Borrowed'}
          </span>
          <span className="inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-900 border border-amber-200/80 shadow-2xs">
            <KarmaIcon className="w-3.5 h-3.5 text-amber-500" />
            <span>{item.owner?.karma ?? item.karma ?? 100} Karma</span>
          </span>
        </div>
      </div>

      {/* Specs / Condition */}
      <div className="mt-6 grid grid-cols-2 sm:grid-cols-3 gap-3">
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
          <p className="text-[11px] text-slate-400 font-medium uppercase">Condition</p>
          <p className="text-sm font-semibold text-slate-800 mt-0.5">{item.condition || 'Not specified'}</p>
        </div>
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
          <p className="text-[11px] text-slate-400 font-medium uppercase">Exchange Zone</p>
          <p className="text-sm font-semibold text-slate-800 mt-0.5">{item.zone || 'Campus Center'}</p>
        </div>
        <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 col-span-2 sm:col-span-1">
          <p className="text-[11px] text-slate-400 font-medium uppercase">Listing ID</p>
          <p className="text-sm font-semibold text-slate-800 mt-0.5">#{item.id}</p>
        </div>
      </div>

      {/* Description */}
      <div className="mt-6 border-t border-slate-100 pt-5">
        <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide">Description</h3>
        <p className="text-slate-600 text-sm mt-2 leading-relaxed whitespace-pre-line">
          {item.description || 'No detailed description provided by student.'}
        </p>
        {item.specs && (
          <div className="mt-3 p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs text-slate-600 font-mono">
            {item.specs}
          </div>
        )}
      </div>

      {/* Owner Info Card */}
      <div className="mt-6 border-t border-slate-100 pt-5 flex items-center justify-between bg-slate-50/80 p-4 rounded-2xl border border-slate-200/60">
        <div>
          <p className="text-xs text-slate-400 font-medium">LISTED BY STUDENT</p>
          <p className="text-base font-bold text-slate-800 mt-0.5">{item.owner?.name}</p>
          <p className="text-xs text-slate-500">
            {formatDept(item.owner?.dept)} · Roll: {item.owner?.roll || 'N/A'}
          </p>
        </div>
        {user && !isOwner && (
          <button
            onClick={() => navigate(`/chat?user=${item.owner_id}&item=${item.id}`)}
            className="bg-white border border-slate-200 text-blue-600 font-semibold px-4 py-2 rounded-xl text-xs shadow-sm hover:bg-blue-50 transition flex items-center gap-1.5"
          >
            <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <span>Contact Owner</span>
          </button>
        )}
      </div>

      {/* Actions Bar */}
      <div className="mt-8 flex flex-col sm:flex-row gap-3">
        {user && item.is_available && !isOwner && (
          <>
            <button
              onClick={() => setShowRequestModal(true)}
              className="flex-1 bg-blue-600 text-white py-3.5 px-6 rounded-xl font-bold hover:bg-blue-700 transition shadow-sm text-sm"
            >
              Request to Borrow
            </button>
            <button
              onClick={() => navigate(`/chat?user=${item.owner_id}&item=${item.id}`)}
              className="bg-slate-100 text-slate-700 py-3.5 px-6 rounded-xl font-bold hover:bg-slate-200 transition text-sm flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <span>Chat / Ask Question</span>
            </button>
          </>
        )}

        {/* Owner Management Buttons */}
        {isOwner && (
          <div className="flex-1 flex gap-3">
            <button
              onClick={handleOpenEdit}
              className="flex-1 bg-amber-500 text-white py-3 px-6 rounded-xl font-bold hover:bg-amber-600 transition text-sm flex items-center justify-center gap-1.5 shadow-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
              <span>Edit Listing</span>
            </button>
            <button
              onClick={() => {
                if (window.confirm('Are you sure you want to delete this listing?')) {
                  deleteMutation.mutate();
                }
              }}
              disabled={deleteMutation.isPending}
              className="bg-rose-50 text-rose-600 border border-rose-200 py-3 px-6 rounded-xl font-bold hover:bg-rose-100 transition text-sm flex items-center justify-center gap-1.5"
            >
              <svg className="w-4 h-4 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              <span>{deleteMutation.isPending ? 'Deleting...' : 'Delete'}</span>
            </button>
          </div>
        )}

        {/* Report Button */}
        {user && !isOwner && (
          <button
            onClick={() => setShowReportModal(true)}
            className="text-xs text-slate-400 hover:text-rose-600 py-2 text-center transition flex items-center justify-center gap-1"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>Report Item</span>
          </button>
        )}
      </div>

      {/* Modals */}
      {showRequestModal && (
        <RequestModal itemId={item.id} onClose={() => setShowRequestModal(false)} />
      )}

      {/* Report Modal */}
      {showReportModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-xl">
            <h3 className="text-lg font-bold text-slate-800">Report Listing</h3>
            <p className="text-xs text-slate-500 mt-1">Help keep CampusShare safe for all KUETians.</p>
            <div className="mt-4">
              <label className="text-xs font-semibold text-slate-600">Reason</label>
              <select
                className="w-full mt-1 border border-slate-200 rounded-lg p-2 text-sm outline-none"
                value={reportReason}
                onChange={(e) => setReportReason(e.target.value)}
              >
                <option value="Inappropriate content">Inappropriate content</option>
                <option value="Fake or misleading post">Fake or misleading post</option>
                <option value="Damaged or prohibited item">Damaged or prohibited item</option>
                <option value="Spam / Duplicate">Spam / Duplicate</option>
              </select>
            </div>
            <div className="mt-3">
              <label className="text-xs font-semibold text-slate-600">Details (Optional)</label>
              <textarea
                className="w-full mt-1 border border-slate-200 rounded-lg p-2 text-sm outline-none"
                rows="3"
                placeholder="Explain why this item should be reviewed..."
                value={reportDetails}
                onChange={(e) => setReportDetails(e.target.value)}
              />
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <button
                onClick={() => setShowReportModal(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={() => reportMutation.mutate({ reason: reportReason, details: reportDetails })}
                disabled={reportMutation.isPending}
                className="px-4 py-2 text-xs font-semibold bg-rose-600 text-white rounded-lg hover:bg-rose-700 disabled:opacity-50"
              >
                {reportMutation.isPending ? 'Submitting...' : 'Submit Report'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && editForm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 z-50 overflow-y-auto">
          <div className="bg-white rounded-2xl p-6 max-w-lg w-full shadow-xl my-8">
            <h3 className="text-lg font-bold text-slate-800">Edit Listing</h3>
            <div className="mt-4 space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-600">Title</label>
                <input
                  type="text"
                  className="w-full mt-1 border border-slate-200 rounded-lg p-2 text-sm outline-none"
                  value={editForm.title}
                  onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-600">Category</label>
                <input
                  type="text"
                  className="w-full mt-1 border border-slate-200 rounded-lg p-2 text-sm outline-none"
                  value={editForm.category}
                  onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-600">Description</label>
                <textarea
                  className="w-full mt-1 border border-slate-200 rounded-lg p-2 text-sm outline-none"
                  rows="3"
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs font-semibold text-slate-600">Condition</label>
                  <select
                    className="w-full mt-1 border border-slate-200 rounded-lg p-2 text-sm outline-none"
                    value={editForm.condition}
                    onChange={(e) => setEditForm({ ...editForm, condition: e.target.value })}
                  >
                    <option value="Brand New">Brand New</option>
                    <option value="Like New">Like New</option>
                    <option value="Good">Good</option>
                    <option value="Fair">Fair</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-600">Campus Zone</label>
                  <input
                    type="text"
                    className="w-full mt-1 border border-slate-200 rounded-lg p-2 text-sm outline-none"
                    value={editForm.zone}
                    onChange={(e) => setEditForm({ ...editForm, zone: e.target.value })}
                  />
                </div>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <button
                onClick={() => setShowEditModal(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={() => editMutation.mutate(editForm)}
                disabled={editMutation.isPending}
                className="px-4 py-2 text-xs font-semibold bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {editMutation.isPending ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
