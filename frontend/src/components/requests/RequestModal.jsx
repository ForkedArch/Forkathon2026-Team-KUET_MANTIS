import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../../api/client';
import toast from 'react-hot-toast';

export default function RequestModal({ itemId, onClose }) {
  const [duration, setDuration] = useState(2);
  const [purpose, setPurpose] = useState('');
  const [pickupZone, setPickupZone] = useState('');
  const [message, setMessage] = useState('');

  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (data) => api.post('/requests', data),
    onSuccess: () => {
      toast.success('Request sent!');
      queryClient.invalidateQueries({ queryKey: ['items'] });
      onClose();
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Failed to send request');
    }
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    mutation.mutate({
      item_id: itemId,
      duration_hours: duration,
      purpose,
      pickup_zone: pickupZone,
      message
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">Request to Borrow</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Duration (hours)</label>
            <select
              className="w-full border rounded px-3 py-2"
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
            >
              <option value={1}>1 hour</option>
              <option value={2}>2 hours</option>
              <option value={4}>4 hours</option>
              <option value={8}>8 hours</option>
              <option value={24}>24 hours</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Purpose</label>
            <input
              type="text"
              className="w-full border rounded px-3 py-2"
              placeholder="e.g., Lab exam"
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Pickup Zone</label>
            <input
              type="text"
              className="w-full border rounded px-3 py-2"
              placeholder="e.g., CSE Building"
              value={pickupZone}
              onChange={(e) => setPickupZone(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Message (optional)</label>
            <textarea
              className="w-full border rounded px-3 py-2"
              rows="2"
              placeholder="Any extra info..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
          </div>
          <div className="flex justify-end space-x-2">
            <button type="button" onClick={onClose} className="px-4 py-2 border rounded">Cancel</button>
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700" disabled={mutation.isPending}>
              {mutation.isPending ? 'Sending...' : 'Send Request'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}