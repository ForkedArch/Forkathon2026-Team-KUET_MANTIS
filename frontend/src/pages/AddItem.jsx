import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api/client';
import toast from 'react-hot-toast';

export default function AddItem() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('Calculators');
  const [description, setDescription] = useState('');
  const [condition, setCondition] = useState('Good');
  const [zone, setZone] = useState('');
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState('');

  const mutation = useMutation({
    mutationFn: (formData) => api.post('/items', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
    onSuccess: () => {
      toast.success('Item added successfully!');
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
    formData.append('title', title);
    formData.append('category', category);
    formData.append('description', description);
    formData.append('condition', condition);
    formData.append('zone', zone);
    if (image) {
      formData.append('image', image);
    }
    mutation.mutate(formData);
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Add New Item</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Title *</label>
          <input
            type="text"
            required
            className="w-full border rounded px-3 py-2"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Category *</label>
          <select
            required
            className="w-full border rounded px-3 py-2"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option>Calculators</option>
            <option>Chargers</option>
            <option>Books</option>
            <option>Lab Equipment</option>
            <option>Others</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Description</label>
          <textarea
            className="w-full border rounded px-3 py-2"
            rows="3"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Condition</label>
          <select
            className="w-full border rounded px-3 py-2"
            value={condition}
            onChange={(e) => setCondition(e.target.value)}
          >
            <option>Like New</option>
            <option>Good</option>
            <option>Fair</option>
            <option>Needs Repair</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Zone (e.g., CSE Building)</label>
          <input
            type="text"
            className="w-full border rounded px-3 py-2"
            value={zone}
            onChange={(e) => setZone(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Image</label>
          <input
            type="file"
            accept="image/*"
            onChange={handleImageChange}
          />
          {imagePreview && (
            <img src={imagePreview} alt="Preview" className="mt-2 h-40 object-cover rounded" />
          )}
        </div>
        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700"
          disabled={mutation.isPending}
        >
          {mutation.isPending ? 'Adding...' : 'Add Item'}
        </button>
      </form>
    </div>
  );
}