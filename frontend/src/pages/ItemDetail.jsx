import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import api, { API_ORIGIN } from '../api/client';
import Loader from '../components/common/Loader';
import RequestModal from '../components/requests/RequestModal';
import { useAuth } from '../context/AuthContext';
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
            className="absolute top-4 right-4 bg-white/90 backdrop-blur p-2.5 rounded-full shadow-md hover:bg-white text-rose-600 transition"
            title="Save to Wishlist"
          >
            <span className="text-lg">❤️</span>
          </button>
        )}
      </div>

      {/* Main Info */}
      <div className="mt-6 flex items-start justify-between gap-4">
        <div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-blue-50 text-blue-700 uppercase tracking-wider">
            {item.type === 'lend' ? '🤝 For Lend' : '📢 Needed (Borrow Beacon)'}
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 mt-2">{item.title}</h1>
          <p className="text-sm text-slate-500 mt-1">
            {item.category} · 📍 {item.zone || 'Anywhere on Campus'}
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
          <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-900 border border-amber-200">
            ⚡ {item.owner?.karma ?? item.karma ?? 100} Karma
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
            {item.owner?.dept ? `Dept ${item.owner.dept}` : 'KUET'} · Roll: {item.owner?.roll || 'N/A'}
          </p>
        </div>
        {user && !isOwner && (
          <button
            onClick={() => navigate(`/chat?user=${item.owner_id}&item=${item.id}`)}
            className="bg-white border border-slate-200 text-blue-600 font-semibold px-4 py-2 rounded-xl text-xs shadow-sm hover:bg-blue-50 transition flex items-center gap-1.5"
          >
            <span>💬</span> Contact Owner
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
              <span>💬</span> Chat / Ask Question
            </button>
          </>
        )}

        {/* Owner Management Buttons */}
        {isOwner && (
          <div className="flex-1 flex gap-3">
            <button
              onClick={handleOpenEdit}
              className="flex-1 bg-amber-500 text-white py-3 px-6 rounded-xl font-bold hover:bg-amber-600 transition text-sm flex items-center justify-center gap-1.5"
            >
              <span>✏️</span> Edit Listing
            </button>
            <button
              onClick={() => {
                if (window.confirm('Are you sure you want to delete this listing?')) {
                  deleteMutation.mutate();
                }
              }}
              disabled={deleteMutation.isPending}
              className="bg-rose-50 text-rose-600 border border-rose-200 py-3 px-6 rounded-xl font-bold hover:bg-rose-100 transition text-sm"
            >
              {deleteMutation.isPending ? 'Deleting...' : '🗑️ Delete'}
            </button>
          </div>
        )}

        {/* Report Button */}
        {user && !isOwner && (
          <button
            onClick={() => setShowReportModal(true)}
            className="text-xs text-slate-400 hover:text-rose-600 py-2 text-center transition"
          >
            🚨 Report Item
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
