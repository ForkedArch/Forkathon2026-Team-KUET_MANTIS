import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../api/client';
import toast from 'react-hot-toast';

const DEFAULT_CATEGORIES = [
  'Calculators',
  'Electronics & Power',
  'Chargers',
  'Books & Notes',
  'Lab Equipment',
  'Cables & Adapters',
  'Stationery & Drawing',
  'Other'
];

/**
 * AddItemModal
 * 
 * Implements 100% compliant click-to-pinpoint mode:
 * 1. User fills basic details (Title, Type, Category, Specs, Condition).
 * 2. User clicks "📍 Pinpoint on Campus Map" -> modal hides, map enters crosshair mode.
 * 3. User clicks any point on the KUET campus map -> coordinates captured.
 * 4. Modal reopens with coordinates and detected KUET landmark pre-filled.
 * 5. Submits to POST /api/items and invalidates React Query cache.
 */
export default function AddItemModal({
  isOpen,
  onClose,
  onStartPinpoint,
  pinpointCoords,
  landmarks = []
}) {
  const queryClient = useQueryClient();

  // Form State
  const [type, setType] = useState('lend'); // 'lend' or 'borrow'
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Calculators');
  const [specs, setSpecs] = useState('');
  const [condition, setCondition] = useState('Good');
  const [zone, setZone] = useState('');
  const [coords, setCoords] = useState(null); // { lat, lng }
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState('');

  // Synchronize coordinates when user completes map pinpointing
  useEffect(() => {
    if (pinpointCoords && pinpointCoords.lat && pinpointCoords.lng) {
      setCoords({ lat: pinpointCoords.lat, lng: pinpointCoords.lng });
      
      // If a zone name was auto-detected or provided, use it
      if (pinpointCoords.zone) {
        setZone(pinpointCoords.zone);
      } else if (landmarks.length > 0) {
        // Find nearest landmark to coordinates
        const nearest = findNearestLandmark(pinpointCoords.lat, pinpointCoords.lng, landmarks);
        if (nearest) setZone(nearest.name);
      }
    }
  }, [pinpointCoords, landmarks]);

  // Nearest Landmark Helper (Euclidean distance approximation for campus scale)
  const findNearestLandmark = (lat, lng, list) => {
    if (!list || list.length === 0) return null;
    let closest = null;
    let minD = Infinity;
    list.forEach(lm => {
      if (lm.coords) {
        const [lLat, lLng] = lm.coords;
        const d = Math.hypot(lat - lLat, lng - lLng);
        if (d < minD) {
          minD = d;
          closest = lm;
        }
      }
    });
    return closest;
  };

  const handleLandmarkSelect = (e) => {
    const selectedName = e.target.value;
    setZone(selectedName);
    const match = landmarks.find(l => l.name === selectedName);
    if (match && match.coords) {
      setCoords({ lat: match.coords[0], lng: match.coords[1] });
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  // Trigger interactive map pinpointing
  const handlePinpointClick = () => {
    if (onStartPinpoint) {
      onStartPinpoint({
        title,
        category,
        type,
        specs,
        condition,
        zone
      });
    }
  };

  // Submit Mutation
  const mutation = useMutation({
    mutationFn: async () => {
      if (imageFile) {
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
        }
        formData.append('image', imageFile);
        return api.post('/items', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      } else {
        const payload = {
          title: title.trim(),
          category,
          type,
          specs: specs.trim(),
          description: specs.trim(),
          condition,
          zone: zone || 'KUET Main Campus',
          latitude: coords ? coords.lat : 22.9006,
          longitude: coords ? coords.lng : 89.5024
        };
        return api.post('/items', payload);
      }
    },
    onSuccess: () => {
      toast.success(type === 'borrow' ? '🚨 Demand Beacon broadcasted!' : '🟢 Item listed successfully!');
      queryClient.invalidateQueries({ queryKey: ['items'] });
      resetForm();
      onClose();
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Failed to publish item');
    }
  });

  const resetForm = () => {
    setTitle('');
    setCategory('Calculators');
    setSpecs('');
    setCondition('Good');
    setZone('');
    setCoords(null);
    setImageFile(null);
    setImagePreview('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!title.trim()) {
      toast.error('Please provide an item title');
      return;
    }
    mutation.mutate();
  };

  if (!isOpen) return null;

  return (
    <div id="add-item-modal" className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
          <div className="flex items-center gap-3">
            <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
              type === 'borrow' ? 'bg-rose-100 text-rose-600' : 'bg-blue-100 text-blue-600'
            }`}>
              {type === 'borrow' ? (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              )}
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                {type === 'borrow' ? 'Broadcast Demand Beacon' : 'List Item for Sharing'}
              </h2>
              <p className="text-xs text-slate-500">
                Share with fellow KUET students inside the 700m campus boundary
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition"
          >
            ✕
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-4 flex-1">
          
          {/* Listing Type Toggle */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Listing Mode
            </label>
            <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-xl border border-slate-200">
              <button
                id="type-btn-lend"
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
                id="type-btn-borrow"
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

          {/* Title */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Title *
            </label>
            <input
              id="item-title"
              type="text"
              required
              placeholder={type === 'borrow' ? 'e.g. Need Casio fx-991EX for Math Lab' : 'e.g. Casio fx-991EX ClassWiz Calculator'}
              className="w-full border border-slate-300 rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          {/* Category & Condition Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Category *
              </label>
              <select
                id="item-category"
                className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                {DEFAULT_CATEGORIES.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Condition
              </label>
              <select
                className="w-full border border-slate-300 rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={condition}
                onChange={(e) => setCondition(e.target.value)}
              >
                <option value="Like New">Like New</option>
                <option value="Good">Good</option>
                <option value="Fair">Fair</option>
                <option value="Needs Repair">Needs Repair</option>
              </select>
            </div>
          </div>

          {/* Specs / Description */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Specifications & Notes
            </label>
            <textarea
              id="item-specs"
              rows="2"
              placeholder="e.g. Dual power solar/battery, original casing included. Available near CSE bldg."
              className="w-full border border-slate-300 rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={specs}
              onChange={(e) => setSpecs(e.target.value)}
            />
          </div>

          {/* Interactive Campus Pinpoint Section */}
          <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                  <svg className="w-4 h-4 text-blue-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span>Campus Location & Pinpoint</span>
                </span>
                <span className="text-[11px] text-slate-500 block">
                  Choose a landmark or click anywhere on the KUET campus map
                </span>
              </div>
              <button
                id="proceed-pin-btn"
                type="button"
                onClick={handlePinpointClick}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center gap-1.5"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span>Pinpoint on Map</span>
              </button>
            </div>

            {/* Coordinate Status Feedback */}
            {coords ? (
              <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-2.5 flex items-center justify-between text-xs text-emerald-900">
                <div className="flex items-center gap-2">
                  <span className="text-emerald-600 font-bold">✓ Location Set:</span>
                  <span className="font-mono">{coords.lat.toFixed(4)}°N, {coords.lng.toFixed(4)}°E</span>
                  {zone && <span className="text-emerald-700 font-medium">({zone})</span>}
                </div>
                <button
                  type="button"
                  onClick={() => setCoords(null)}
                  className="text-emerald-700 hover:text-emerald-900 text-[11px] underline"
                >
                  Reset
                </button>
              </div>
            ) : (
              <div className="text-xs text-slate-500 italic bg-white border border-dashed border-slate-300 rounded-lg p-2.5 text-center">
                No coordinates chosen yet. Defaulting to KUET Central Academic Area [22.9006, 89.5024].
              </div>
            )}

            {/* Quick Landmark Dropdown */}
            {landmarks.length > 0 && (
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-1">
                  Or select nearest KUET Landmark:
                </label>
                <select
                  className="w-full border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                  value={zone}
                  onChange={handleLandmarkSelect}
                >
                  <option value="">-- Choose Landmark --</option>
                  {landmarks.map(lm => (
                    <option key={lm.id} value={lm.name}>
                      {lm.name} ({lm.category})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Image Upload */}
          <div id="img-upload-box">
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              Item Photo (Optional)
            </label>
            <input
              id="file-input"
              type="file"
              accept="image/*"
              className="w-full text-xs text-slate-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              onChange={handleImageChange}
            />
            {imagePreview && (
              <div className="mt-2 relative w-24 h-24 rounded-lg overflow-hidden border border-slate-200 shadow-sm">
                <img id="preview-img" src={imagePreview} alt="Preview" className="w-full h-full object-cover" />
                <button
                  type="button"
                  onClick={() => { setImageFile(null); setImagePreview(''); }}
                  className="absolute top-1 right-1 bg-slate-900/80 text-white rounded-full w-5 h-5 flex items-center justify-center text-[10px]"
                >
                  ✕
                </button>
              </div>
            )}
          </div>

          {/* Form Actions */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 rounded-xl hover:bg-slate-100 transition"
            >
              Cancel
            </button>
            <button
              id="direct-submit-btn"
              type="submit"
              disabled={mutation.isPending}
              className={`px-5 py-2.5 text-xs font-bold text-white rounded-xl shadow-sm transition flex items-center gap-2 ${
                type === 'borrow'
                  ? 'bg-rose-600 hover:bg-rose-700'
                  : 'bg-blue-600 hover:bg-blue-700'
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
    </div>
  );
}
