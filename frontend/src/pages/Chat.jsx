import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState, useMemo } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { formatDept } from '../utils/dept';
import toast from 'react-hot-toast';

export default function Chat() {
  const { requestId } = useParams();
  const [searchParams] = useSearchParams();
  const rawTargetUser = searchParams.get('user');
  const targetUserId = rawTargetUser && !isNaN(parseInt(rawTargetUser, 10))
    ? parseInt(rawTargetUser, 10)
    : null;
  const targetItemId = searchParams.get('item');
  const navigate = useNavigate();
  const { user } = useAuth();

  const [activeUserId, setActiveUserId] = useState(targetUserId || null);
  const [message, setMessage] = useState('');
  const [localMessages, setLocalMessages] = useState([]);
  // Mobile: 'list' shows sidebar, 'chat' shows message panel
  const [mobileView, setMobileView] = useState(targetUserId || requestId ? 'chat' : 'list');
  const queryClient = useQueryClient();
  const bottomRef = useRef(null);

  // Fetch all user conversations
  const { data: rawConversations = [], isLoading: loadingConversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: async () => {
      try {
        const res = await api.get('/chat/conversations');
        return Array.isArray(res.data) ? res.data : [];
      } catch (err) {
        console.warn('Failed to fetch backend conversations:', err);
        return [];
      }
    },
    refetchInterval: 3000,
  });

  const conversations = useMemo(() => {
    return Array.isArray(rawConversations) ? rawConversations : [];
  }, [rawConversations]);

  // Fetch campus items to discover other students
  const { data: rawItems = [] } = useQuery({
    queryKey: ['items-students'],
    queryFn: async () => {
      try {
        const res = await api.get('/items');
        return Array.isArray(res.data) ? res.data : [];
      } catch {
        return [];
      }
    },
    staleTime: 1000 * 60 * 5,
  });

  // Extract unique campus peers from items
  const campusPeers = useMemo(() => {
    const peersMap = new Map();
    if (Array.isArray(rawItems)) {
      rawItems.forEach((item) => {
        if (item.owner && item.owner.id && (!user || item.owner.id !== user.id)) {
          peersMap.set(item.owner.id, {
            id: item.owner.id,
            name: item.owner.name || 'KUET Student',
            dept: item.owner.dept || 'KUET',
            roll: item.owner.roll || '???',
            karma: item.owner.karma || 100,
          });
        }
      });
    }
    return Array.from(peersMap.values());
  }, [rawItems, user]);

  // Sync activeUserId from URL param
  useEffect(() => {
    if (targetUserId) {
      setActiveUserId(targetUserId);
      setMobileView('chat');
    } else if (!activeUserId && !requestId && conversations.length > 0) {
      setActiveUserId(conversations[0].contact?.id);
    }
  }, [targetUserId, conversations]);

  // Messages Query
  const {
    data: rawMessages = [],
    isLoading: loadingMessages,
    isError,
  } = useQuery({
    queryKey: ['messages', requestId || `user-${activeUserId}`],
    queryFn: async () => {
      try {
        if (requestId) {
          const res = await api.get(`/chat/${requestId}/messages`);
          return Array.isArray(res.data) ? res.data : [];
        }
        if (activeUserId) {
          const res = await api.get(`/chat/direct/${activeUserId}`);
          return Array.isArray(res.data) ? res.data : [];
        }
      } catch (err) {
        console.warn('Failed to fetch messages:', err);
      }
      return [];
    },
    refetchInterval: 2500,
    enabled: !!requestId || (!!activeUserId && !isNaN(activeUserId)),
  });

  // Load local storage messages as offline fallback
  useEffect(() => {
    if (activeUserId) {
      try {
        const stored = localStorage.getItem(`offline_chat_${activeUserId}`);
        setLocalMessages(stored ? JSON.parse(stored) : []);
      } catch {
        setLocalMessages([]);
      }
    }
  }, [activeUserId]);

  // Combine server + local optimistic messages
  const messages = useMemo(() => {
    const serverMsgs = Array.isArray(rawMessages) ? rawMessages : [];
    const serverIds = new Set(serverMsgs.map((m) => m.id));
    const pendingLocal = localMessages.filter((m) => !serverIds.has(m.id));
    return [...serverMsgs, ...pendingLocal];
  }, [rawMessages, localMessages]);

  // Resolve active contact info
  const activeConversation = conversations.find((c) => c.contact?.id === activeUserId);
  const knownPeer = campusPeers.find((p) => p.id === activeUserId);

  const { data: targetUserProfile } = useQuery({
    queryKey: ['user-public', activeUserId],
    queryFn: () => api.get(`/auth/user/${activeUserId}`).then((res) => res.data).catch(() => null),
    enabled: !!activeUserId && !activeConversation?.contact && !knownPeer,
  });

  const activeContact =
    activeConversation?.contact ||
    knownPeer ||
    targetUserProfile ||
    (messages.length > 0
      ? (messages[0].sender_id !== user?.id ? messages[0].sender : messages[0].recipient)
      : null);

  // Send Mutation with Optimistic & Offline Fallback
  const sendMutation = useMutation({
    mutationFn: async (content) => {
      try {
        if (requestId) {
          return await api.post(`/chat/${requestId}/messages`, { content });
        }
        return await api.post(`/chat/direct/${activeUserId}`, {
          content,
          item_id: targetItemId ? parseInt(targetItemId, 10) : undefined,
        });
      } catch (err) {
        // Offline fallback
        const optimisticMsg = {
          id: `local_${Date.now()}`,
          sender_id: user?.id || 999,
          recipient_id: activeUserId,
          content,
          created_at: new Date().toISOString(),
          sender: user || { name: 'You' },
        };
        const updated = [...localMessages, optimisticMsg];
        setLocalMessages(updated);
        try { localStorage.setItem(`offline_chat_${activeUserId}`, JSON.stringify(updated)); } catch {}
        return { data: optimisticMsg };
      }
    },
    onSuccess: () => {
      setMessage('');
      queryClient.invalidateQueries({ queryKey: ['messages', requestId || `user-${activeUserId}`] });
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Failed to send message');
    },
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

  const selectConversation = (userId) => {
    setActiveUserId(userId);
    setMobileView('chat');
    navigate(`/chat?user=${userId}`);
  };

  const isChattingWithSelf = user && activeUserId && activeUserId === user.id;
  const hasActiveChat = !!activeUserId || !!requestId;

  // ── SIDEBAR PANEL ──────────────────────────────────────────────────────────
  const SidebarPanel = () => (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
      <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
        <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
          💬 Messages
        </h2>
        <span className="text-xs bg-blue-100 text-blue-700 font-semibold px-2 py-0.5 rounded-full">
          {conversations.length}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
        {loadingConversations && conversations.length === 0 && (
          <p className="text-sm text-slate-400 p-4 text-center">Loading...</p>
        )}

        {conversations.map((conv) => {
          const isSelected = activeUserId === conv.contact?.id;
          return (
            <button
              key={conv.contact?.id}
              onClick={() => selectConversation(conv.contact?.id)}
              className={`w-full text-left p-3.5 flex items-start gap-3 transition-colors hover:bg-slate-50 ${
                isSelected ? 'bg-blue-50/80 border-l-4 border-blue-600' : ''
              }`}
            >
              <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-bold flex items-center justify-center shrink-0 text-sm">
                {(conv.contact?.name?.[0] || 'U').toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-slate-800 truncate">{conv.contact?.name}</p>
                  <span className="text-[10px] text-slate-400 shrink-0">
                    {conv.last_message_at
                      ? new Date(conv.last_message_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                      : ''}
                  </span>
                </div>
                <p className="text-xs text-blue-600 font-semibold truncate mt-0.5">
                  {conv.contact?.dept ? formatDept(conv.contact.dept) : 'KUET Student'}
                </p>
                <p className="text-xs text-slate-500 truncate mt-0.5">{conv.last_message}</p>
              </div>
              {conv.unread_count > 0 && (
                <span className="w-5 h-5 rounded-full bg-blue-600 text-white text-[10px] font-bold flex items-center justify-center shrink-0">
                  {conv.unread_count}
                </span>
              )}
            </button>
          );
        })}

        {conversations.length === 0 && !loadingConversations && campusPeers.length === 0 && (
          <p className="text-xs text-slate-400 p-4 text-center">No conversations yet. Browse items and send a request to start chatting!</p>
        )}

        {/* Campus peers from listings */}
        {campusPeers.length > 0 && (
          <div className="p-3 bg-slate-50/60">
            <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-1 mb-2">
              Campus Students
            </p>
            <div className="space-y-1">
              {campusPeers.map((peer) => {
                const isSelected = activeUserId === peer.id;
                return (
                  <button
                    key={peer.id}
                    onClick={() => selectConversation(peer.id)}
                    className={`w-full text-left p-2 rounded-xl flex items-center gap-2.5 transition text-xs ${
                      isSelected
                        ? 'bg-blue-600 text-white font-semibold'
                        : 'hover:bg-slate-200/60 text-slate-700'
                    }`}
                  >
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${
                      isSelected ? 'bg-white text-blue-600' : 'bg-blue-100 text-blue-700'
                    }`}>
                      {(peer.name[0] || 'U').toUpperCase()}
                    </div>
                    <span className="truncate flex-1 font-medium">{peer.name}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      isSelected ? 'bg-blue-700 text-blue-100' : 'bg-slate-100 text-slate-500'
                    }`}>
                      {formatDept(peer.dept)}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );

  // ── CHAT PANEL ─────────────────────────────────────────────────────────────
  const ChatPanel = () => (
    <div className="flex flex-col h-full bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
      {hasActiveChat ? (
        <>
          {/* Header */}
          <div className="p-3 px-4 border-b border-slate-100 flex items-center gap-3 bg-slate-50/50">
            {/* Back button on mobile */}
            <button
              onClick={() => setMobileView('list')}
              className="md:hidden p-1.5 rounded-lg hover:bg-slate-200 text-slate-600 shrink-0"
              aria-label="Back to conversations"
            >
              ←
            </button>
            <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-sm shrink-0">
              {(activeContact?.name?.[0] || 'S').toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-bold text-slate-800 truncate">
                {activeContact?.name || (requestId ? `Request #${requestId}` : 'Select a student')}
              </h3>
              <p className="text-xs text-slate-500 truncate">
                {activeContact?.roll ? `Roll: ${activeContact.roll}` : 'KUET Student'}
                {activeContact?.dept && ` · ${formatDept(activeContact.dept)}`}
              </p>
            </div>
            <span className="inline-flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-full bg-amber-50 text-amber-900 border border-amber-200 shrink-0">
              ⚡ {activeContact?.karma || 100}
            </span>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50/30">
            {loadingMessages && messages.length === 0 && (
              <div className="h-full flex items-center justify-center text-sm text-slate-400">
                Loading messages...
              </div>
            )}

            {isError && (
              <div className="p-3 bg-amber-50 text-amber-800 rounded-xl text-xs text-center border border-amber-200">
                Connection issue — messages will sync when back online.
              </div>
            )}

            {!loadingMessages && messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-sm py-12">
                <span className="text-3xl mb-2">👋</span>
                <p className="font-semibold text-slate-700">No messages yet.</p>
                <p className="text-xs text-slate-400 mt-1">Send a message below to get started.</p>
              </div>
            )}

            {messages.map((msg, idx) => {
              const isMine = msg.sender_id === user?.id || String(msg.id).startsWith('local_');
              return (
                <div key={msg.id || idx} className={`flex flex-col ${isMine ? 'items-end' : 'items-start'}`}>
                  <div className={`px-4 py-2.5 rounded-2xl max-w-[80%] text-sm shadow-sm ${
                    isMine
                      ? 'bg-blue-600 text-white rounded-br-sm'
                      : 'bg-white text-slate-800 border border-slate-200 rounded-bl-sm'
                  }`}>
                    <p className="break-words leading-relaxed">{msg.content}</p>
                  </div>
                  <span className="text-[10px] text-slate-400 px-1 mt-1">
                    {msg.created_at
                      ? new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                      : 'Just now'}
                  </span>
                </div>
              );
            })}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          {isChattingWithSelf ? (
            <div className="p-4 border-t border-amber-100 bg-amber-50 text-amber-800 text-xs font-medium text-center">
              ℹ️ You cannot message yourself.
            </div>
          ) : (
            <form onSubmit={handleSend} className="p-3 border-t border-slate-100 flex gap-2 bg-white">
              <input
                type="text"
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
                placeholder={`Message ${activeContact?.name?.split(' ')[0] || 'student'}...`}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                autoFocus
              />
              <button
                type="submit"
                disabled={sendMutation.isPending || !message.trim()}
                className="bg-blue-600 text-white px-5 py-2.5 rounded-xl hover:bg-blue-700 disabled:opacity-50 text-sm font-semibold transition shadow-sm"
              >
                {sendMutation.isPending ? '...' : 'Send'}
              </button>
            </form>
          )}
        </>
      ) : (
        <div className="h-full flex flex-col items-center justify-center text-slate-500 p-6">
          <span className="text-4xl mb-3">💬</span>
          <h3 className="font-bold text-slate-800 text-base">Select a Conversation</h3>
          <p className="text-xs text-slate-400 mt-1 text-center max-w-xs">
            Choose a student from the list or message someone from your Borrow Requests.
          </p>
          {/* Mobile: show list button */}
          <button
            onClick={() => setMobileView('list')}
            className="mt-4 md:hidden px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold"
          >
            View Conversations
          </button>
        </div>
      )}
    </div>
  );

  return (
    <div className="h-full w-full p-2 sm:p-4 flex gap-4 overflow-hidden">
      {/* Desktop: show both panels side by side */}
      {/* Mobile: show only the active panel */}
      <div className={`w-full md:w-72 shrink-0 ${mobileView === 'list' ? 'flex' : 'hidden'} md:flex flex-col`}>
        <SidebarPanel />
      </div>
      <div className={`flex-1 min-w-0 ${mobileView === 'chat' ? 'flex' : 'hidden'} md:flex flex-col`}>
        <ChatPanel />
      </div>
    </div>
  );
}
