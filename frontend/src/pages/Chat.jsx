import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

export default function Chat() {
  const { requestId } = useParams();
  const { user } = useAuth();
  const [message, setMessage] = useState('');
  const queryClient = useQueryClient();

  // Polling every 3 seconds
  const { data: messages, isLoading } = useQuery({
    queryKey: ['messages', requestId],
    queryFn: () => api.get(`/chat/${requestId}/messages`).then(res => res.data),
    refetchInterval: 3000,
    enabled: !!requestId
  });

  const sendMutation = useMutation({
    mutationFn: (content) => api.post(`/chat/${requestId}/messages`, { content }),
    onSuccess: () => {
      setMessage('');
      queryClient.invalidateQueries({ queryKey: ['messages', requestId] });
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed to send')
  });

  const handleSend = (e) => {
    e.preventDefault();
    if (message.trim()) {
      sendMutation.mutate(message);
    }
  };

  if (isLoading) return <div>Loading chat...</div>;

  return (
    <div className="max-w-2xl mx-auto p-6 h-screen flex flex-col">
      <h2 className="text-xl font-bold mb-4">Chat</h2>
      <div className="flex-1 overflow-y-auto border rounded p-4 bg-gray-50 flex flex-col space-y-2">
        {messages?.map(msg => (
          <div
            key={msg.id}
            className={`p-2 rounded max-w-[75%] ${msg.sender_id === user.id ? 'bg-blue-100 self-end' : 'bg-white self-start'}`}
          >
            <p className="text-sm font-semibold">{msg.sender.name}</p>
            <p>{msg.content}</p>
            <p className="text-xs text-gray-500">{new Date(msg.created_at).toLocaleTimeString()}</p>
          </div>
        ))}
      </div>
      <form onSubmit={handleSend} className="mt-4 flex gap-2">
        <input
          type="text"
          className="flex-1 border rounded px-4 py-2"
          placeholder="Type a message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button type="submit" className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700">
          Send
        </button>
      </form>
    </div>
  );
}