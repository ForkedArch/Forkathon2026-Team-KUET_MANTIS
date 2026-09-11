import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../api/client';
import toast from 'react-hot-toast';

export default function AddItem() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [type, setType] = useState('lend');
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Calculators');
  const [specs, setSpecs] = useState('');
  const [condition, setCondition] = useState('Good');
  const [zone, setZone] = useState('');
  const [coords, setCoords] = useState(null);
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState('');

  // Fetch landmarks for dropdown
  const { data: landmarksData } = useQuery({
    queryKey: ['landmarks'],
    queryFn: () => api.get('/landmarks').then(res => res.data).catch(() => ({ zones: [] }))
  });
  const landmarks = landmarksData?.zones || [];

  const handleLandmarkSelect = (e) => {
    const selected = e.target.value;
    setZone(selected);
    const match = landmarks.find(l => l.name === selected);
    if (match && match.coords) {
      setCoords({ lat: match.coords[0], lng: match.coords[1] });
    }
  };

  const mutation = useMutation({
    mutationFn: (formData) => api.post('/items', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
    onSuccess: () => {
      toast.success(type === 'borrow' ? 'Demand Beacon broadcasted successfully!' : 'Item listed successfully!');
      queryClient.invalidateQueries({ queryKey: ['items'] });
      navigate('/');
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Failed to add item');
    }
  });

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('title', title.trim());
    formData.append('category', category);
    formData.append('type', type);
    formData.append('specs', specs.trim());
    formData.append('description', specs.trim());
    formData.append('condition', condition);
    formData.append('zone', zone || 'KUET Main Campus');
    if (coords) {
      formData.append('latitude', coords.lat);
      formData.append('longitude', coords.lng);
    } else {
      formData.append('latitude', 22.9006);
      formData.append('longitude', 89.5024);
    }
    if (image) {
      formData.append('image', image);
    }
    mutation.mutate(formData);
  };

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6 h-full overflow-y-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Add New Campus Listing</h1>
          <p className="text-xs text-slate-500">List an item for sharing or broadcast an active demand beacon</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        {/* Listing Mode Toggle */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
            Listing Mode
          </label>
          <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-xl border border-slate-200">
            <button
              type="button"
              onClick={() => setType('lend')}
              className={`py-2 px-4 rounded-lg text-xs font-bold transition flex items-center justify-center gap-2 ${
                type === 'lend'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${type === 'lend' ? 'bg-white' : 'bg-emerald-500'}`}></span>
              <span>I have an item to Lend</span>
            </button>
            <button
              type="button"
              onClick={() => setType('borrow')}
              className={`py-2 px-4 rounded-lg text-xs font-bold transition flex items-center justify-center gap-2 ${
                type === 'borrow'
                  ? 'bg-rose-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <svg className={`w-3.5 h-3.5 ${type === 'borrow' ? 'text-white' : 'text-rose-600'}`} fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
              </svg>
              <span>I need to Borrow (Beacon)</span>
            </button>
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Title *</label>
          <input
            type="text"
            required
            className="w-full border border-slate-300 rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder={type === 'borrow' ? 'e.g. Need Casio fx-991EX Calculator' : 'e.g. Casio fx-991EX ClassWiz Calculator'}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Category *</label>
            <select
              required
              className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option>Calculators</option>
              <option>Electronics & Power</option>
              <option>Chargers</option>
              <option>Books & Notes</option>
              <option>Lab Equipment</option>
              <option>Cables & Adapters</option>
              <option>Stationery & Drawing</option>
              <option>Other</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Condition</label>
            <select
              className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={condition}
              onChange={(e) => setCondition(e.target.value)}
            >
              <option>Like New</option>
              <option>Good</option>
              <option>Fair</option>
              <option>Needs Repair</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Specifications & Notes</label>
          <textarea
            className="w-full border border-slate-300 rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows="3"
            placeholder="e.g. Fully functional, available for lab classes near CSE building."
            value={specs}
            onChange={(e) => setSpecs(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Campus Zone / Landmark</label>
          {landmarks.length > 0 ? (
            <select
              className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={zone}
              onChange={handleLandmarkSelect}
            >
              <option value="">-- Choose KUET Landmark --</option>
              {landmarks.map(lm => (
                <option key={lm.id} value={lm.name}>{lm.name} ({lm.category})</option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              className="w-full border border-slate-300 rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g. CSE Building, Central Library"
              value={zone}
              onChange={(e) => setZone(e.target.value)}
            />
          )}
          {coords && (
            <p className="text-[11px] text-emerald-600 mt-1 font-medium flex items-center gap-1">
              <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>Selected Coordinates: {coords.lat.toFixed(4)}°N, {coords.lng.toFixed(4)}°E (within 700m KUET boundary)</span>
            </p>
          )}
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Item Photo (Optional)</label>
          <input
            type="file"
            accept="image/*"
            className="w-full text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            onChange={handleImageChange}
          />
          {imagePreview && (
            <div className="mt-2 relative w-28 h-28 rounded-lg overflow-hidden border border-slate-200">
              <img src={imagePreview} alt="Preview" className="w-full h-full object-cover" />
              <button
                type="button"
                onClick={() => { setImage(null); setImagePreview(''); }}
                className="absolute top-1 right-1 bg-slate-900/80 text-white rounded-full w-5 h-5 flex items-center justify-center text-[10px]"
              >
                ✕
              </button>
            </div>
          )}
        </div>

        <div className="pt-2 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 rounded-xl hover:bg-slate-100 transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={mutation.isPending}
            className={`px-6 py-2.5 text-xs font-bold text-white rounded-xl shadow-xs transition flex items-center gap-2 ${
              type === 'borrow' ? 'bg-rose-600 hover:bg-rose-700' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {mutation.isPending ? (
              'Publishing...'
            ) : type === 'borrow' ? (
              <>
                <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
                </svg>
                <span>Broadcast Beacon</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 4v16m8-8H4" />
                </svg>
                <span>List Item</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
