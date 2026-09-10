import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

export default function Chat() {
  const { requestId } = useParams();
  const { user } = useAuth();
  const [message, setMessage] = useState('');
  const queryClient = useQueryClient();
  const bottomRef = useRef(null);

  const { data: messages = [], isLoading, isError, error } = useQuery({
    queryKey: ['messages', requestId],
    queryFn: () => api.get(`/chat/${requestId}/messages`).then((res) => res.data),
    refetchInterval: 3000,
    enabled: !!requestId,
  });

  const sendMutation = useMutation({
    mutationFn: (content) => api.post(`/chat/${requestId}/messages`, { content }),
    onSuccess: () => {
      setMessage('');
      queryClient.invalidateQueries({ queryKey: ['messages', requestId] });
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed to send'),
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (message.trim()) {
      sendMutation.mutate(message.trim());
    }
  };

  if (isLoading) {
    return <div className="h-full flex items-center justify-center text-slate-500">Loading chat...</div>;
  }

  if (isError) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <div className="max-w-md text-center">
          <h2 className="text-xl font-bold mb-2">Chat unavailable</h2>
          <p className="text-red-600">
            {error?.response?.data?.detail || 'Could not load this chat.'}
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Chat unlocks only after the owner accepts the borrow request.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full max-w-2xl mx-auto p-4 sm:p-6 flex flex-col min-h-0">
      <h2 className="text-xl font-bold mb-3 shrink-0">Chat</h2>

      <div className="flex-1 min-h-0 overflow-y-auto border rounded-xl p-4 bg-white flex flex-col space-y-2">
        {messages.length === 0 && (
          <p className="text-sm text-gray-500 text-center my-auto">No messages yet. Say hello.</p>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`p-2 rounded-lg max-w-[75%] ${
              msg.sender_id === user?.id
                ? 'bg-blue-100 self-end'
                : 'bg-slate-100 self-start'
            }`}
          >
            <p className="text-sm font-semibold">{msg.sender?.name || 'Student'}</p>
            <p className="break-words">{msg.content}</p>
            <p className="text-xs text-gray-500">
              {msg.created_at ? new Date(msg.created_at).toLocaleTimeString() : ''}
            </p>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="mt-3 flex gap-2 shrink-0 pb-2">
        <input
          type="text"
          className="flex-1 border border-slate-300 rounded-lg px-4 py-2 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
          placeholder="Type a message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button
          type="submit"
          disabled={sendMutation.isPending || !message.trim()}
          className="bg-blue-600 text-white px-5 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
        >
          {sendMutation.isPending ? '...' : 'Send'}
        </button>
      </form>
    </div>
  );
}
