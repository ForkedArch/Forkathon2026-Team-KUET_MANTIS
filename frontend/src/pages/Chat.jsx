import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { formatDept } from '../utils/dept';
import toast from 'react-hot-toast';

export default function Chat() {
  const { requestId } = useParams();
  const [searchParams] = useSearchParams();
  const targetUserId = searchParams.get('user');
  const targetItemId = searchParams.get('item');
  const navigate = useNavigate();
  const { user } = useAuth();

  const [activeUserId, setActiveUserId] = useState(targetUserId ? parseInt(targetUserId, 10) : null);
  const [message, setMessage] = useState('');
  const queryClient = useQueryClient();
  const bottomRef = useRef(null);

  // Fetch all user conversations
  const { data: conversations = [], isLoading: loadingConversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => api.get('/chat/conversations').then((res) => res.data),
    refetchInterval: 3000,
  });

  // If targetUserId is set via query param, ensure activeUserId matches
  useEffect(() => {
    if (targetUserId) {
      setActiveUserId(parseInt(targetUserId, 10));
    } else if (!activeUserId && !requestId && conversations.length > 0) {
      setActiveUserId(conversations[0].contact?.id);
    }
  }, [targetUserId, conversations, activeUserId, requestId]);

  // Messages Query: Either by direct user or by request_id
  const {
    data: messages = [],
    isLoading: loadingMessages,
    isError,
    error,
  } = useQuery({
    queryKey: ['messages', requestId || `user-${activeUserId}`],
    queryFn: () => {
      if (requestId) {
        return api.get(`/chat/${requestId}/messages`).then((res) => res.data);
      }
      if (activeUserId) {
        return api.get(`/chat/direct/${activeUserId}`).then((res) => res.data);
      }
      return [];
    },
    refetchInterval: 2500,
    enabled: !!requestId || !!activeUserId,
  });

  // Send Mutation
  const sendMutation = useMutation({
    mutationFn: (content) => {
      if (requestId) {
        return api.post(`/chat/${requestId}/messages`, { content });
      }
      return api.post(`/chat/direct/${activeUserId}`, {
        content,
        item_id: targetItemId ? parseInt(targetItemId, 10) : undefined,
      });
    },
    onSuccess: () => {
      setMessage('');
      queryClient.invalidateQueries({ queryKey: ['messages', requestId || `user-${activeUserId}`] });
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed to send message'),
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

  // Find active contact details
  const activeConversation = conversations.find((c) => c.contact?.id === activeUserId);
  const activeContact =
    activeConversation?.contact ||
    (messages.length > 0 && messages[0].sender_id !== user?.id
      ? messages[0].sender
      : messages[0]?.recipient);

  return (
    <div className="h-[calc(100vh-5rem)] max-w-6xl mx-auto p-2 sm:p-4 flex gap-4">
      {/* Left Sidebar: Conversations list */}
      <div className="w-full md:w-80 bg-white border border-slate-200 rounded-2xl flex flex-col shrink-0 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <span>💬</span> Messages
          </h2>
          <span className="text-xs bg-blue-100 text-blue-700 font-semibold px-2 py-0.5 rounded-full">
            {conversations.length}
          </span>
        </div>

        <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
          {loadingConversations && conversations.length === 0 && (
            <p className="text-sm text-slate-400 p-4 text-center">Loading conversations...</p>
          )}

          {!loadingConversations && conversations.length === 0 && (
            <div className="p-6 text-center text-slate-400 text-sm">
              <p>No conversations yet.</p>
              <p className="text-xs mt-1 text-slate-500">
                Click "Contact Owner" on any item listing to start chatting.
              </p>
            </div>
          )}

          {conversations.map((conv) => {
            const isSelected = activeUserId === conv.contact?.id;
            return (
              <button
                key={conv.contact?.id}
                onClick={() => {
                  setActiveUserId(conv.contact?.id);
                  if (requestId) navigate('/chat');
                }}
                className={`w-full text-left p-3.5 flex items-start gap-3 transition-colors hover:bg-slate-50 ${
                  isSelected ? 'bg-blue-50/80 border-l-4 border-blue-600' : ''
                }`}
              >
                <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-bold flex items-center justify-center shrink-0 text-sm shadow-sm">
                  {conv.contact?.name?.[0]?.toUpperCase() || 'U'}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold text-slate-800 truncate">
                      {conv.contact?.name}
                    </p>
                    <span className="text-[10px] text-slate-400 shrink-0">
                      {conv.last_message_at
                        ? new Date(conv.last_message_at).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })
                        : ''}
                    </span>
                  </div>
                  <p className="text-xs font-semibold text-blue-600 truncate mt-0.5">
                    {conv.contact?.dept ? formatDept(conv.contact.dept) : 'KUET Student'}
                  </p>
                  <p className="text-xs text-slate-600 truncate mt-1">
                    {conv.last_message}
                  </p>
                </div>
                {conv.unread_count > 0 && (
                  <span className="w-5 h-5 rounded-full bg-blue-600 text-white text-[10px] font-bold flex items-center justify-center shrink-0">
                    {conv.unread_count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Right Chat Panel */}
      <div className="flex-1 bg-white border border-slate-200 rounded-2xl flex flex-col shadow-sm overflow-hidden">
        {activeUserId || requestId ? (
          <>
            {/* Chat Header */}
            <div className="p-3.5 px-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-sm">
                  {activeContact?.name?.[0]?.toUpperCase() || 'S'}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-800">
                    {activeContact?.name || `Student #${activeUserId || ''}`}
                  </h3>
                  <p className="text-xs text-slate-500">
                    {activeContact?.roll ? `Roll: ${activeContact.roll}` : 'KUET Campus Member'}
                    {activeContact?.dept && ` · ${formatDept(activeContact.dept)}`}
                  </p>
                </div>
              </div>
              {activeContact?.karma && (
                <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full bg-amber-50 text-amber-900 border border-amber-200">
                  ⚡ {activeContact.karma} Karma
                </span>
              )}
            </div>

            {/* Messages Scroll Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50/30">
              {loadingMessages && messages.length === 0 && (
                <div className="h-full flex items-center justify-center text-sm text-slate-400">
                  Loading chat history...
                </div>
              )}

              {isError && (
                <div className="p-4 bg-red-50 text-red-700 rounded-xl text-sm text-center">
                  {error?.response?.data?.detail || 'Could not load messages.'}
                </div>
              )}

              {!loadingMessages && messages.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-slate-400 text-sm">
                  <span className="text-3xl mb-2">👋</span>
                  <p>No messages yet with this student.</p>
                  <p className="text-xs text-slate-400 mt-1">Send a message to coordinate handover or ask questions.</p>
                </div>
              )}

              {messages.map((msg) => {
                const isMine = msg.sender_id === user?.id;
                return (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${isMine ? 'items-end' : 'items-start'}`}
                  >
                    <div
                      className={`px-4 py-2.5 rounded-2xl max-w-[80%] text-sm shadow-sm ${
                        isMine
                          ? 'bg-blue-600 text-white rounded-br-xs'
                          : 'bg-white text-slate-800 border border-slate-200 rounded-bl-xs'
                      }`}
                    >
                      <p className="break-words leading-relaxed">{msg.content}</p>
                    </div>
                    <span className="text-[10px] text-slate-400 px-1 mt-1">
                      {msg.created_at
                        ? new Date(msg.created_at).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })
                        : ''}
                    </span>
                  </div>
                );
              })}
              <div ref={bottomRef} />
            </div>

            {/* Message Input Bar */}
            <form onSubmit={handleSend} className="p-3 border-t border-slate-100 flex gap-2 bg-white">
              <input
                type="text"
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                placeholder="Type your message..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
              />
              <button
                type="submit"
                disabled={sendMutation.isPending || !message.trim()}
                className="bg-blue-600 text-white px-5 py-2.5 rounded-xl hover:bg-blue-700 disabled:opacity-50 text-sm font-semibold transition shadow-sm"
              >
                {sendMutation.isPending ? 'Sending...' : 'Send'}
              </button>
            </form>
          </>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-slate-400">
            <span className="text-4xl mb-2">💬</span>
            <p className="font-semibold text-slate-700">Select a conversation</p>
            <p className="text-xs text-slate-400 mt-1">Choose a student on the left or contact an owner from an item page.</p>
          </div>
        )}
      </div>
    </div>
  );
}
