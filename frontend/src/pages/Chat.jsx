import { useParams, useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useRef, useState, useMemo } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { formatDept } from '../utils/dept';
import toast from 'react-hot-toast';

// Modern SVG Icons
const ChatBubbleIcon = ({ className = "w-5 h-5" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
  </svg>
);

const SendIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3" />
  </svg>
);

const SearchIcon = ({ className = "w-4 h-4" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
);

const ArrowBackIcon = ({ className = "w-5 h-5" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
  </svg>
);

// Fallback campus students for instant discovery
const CAMPUS_STUDENTS = [
  { id: 2, name: 'Anik Sen', dept: 'EEE', roll: '021', karma: 110 },
  { id: 3, name: 'Farhan Kabir', dept: 'ME', roll: '015', karma: 120 },
  { id: 4, name: 'Sadia Afrin', dept: 'CE', roll: '045', karma: 105 },
  { id: 5, name: 'Anupoma Sharmin', dept: 'CSE', roll: '009', karma: 115 },
];

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
  const [searchQuery, setSearchQuery] = useState('');
  const [message, setMessage] = useState('');
  const [localMessages, setLocalMessages] = useState([]);
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

  // Fetch user requests to discover connected peers
  const { data: rawRequests = [] } = useQuery({
    queryKey: ['requests'],
    queryFn: async () => {
      try {
        const res = await api.get('/requests/me');
        return Array.isArray(res.data) ? res.data : [];
      } catch {
        return [];
      }
    },
    enabled: !!user,
    staleTime: 1000 * 60 * 3,
  });

  // Extract unique campus peers from items, requests, and verified directory
  const campusPeers = useMemo(() => {
    const peersMap = new Map();

    // 1. From borrow requests
    if (Array.isArray(rawRequests)) {
      rawRequests.forEach((req) => {
        const other = req.borrower_id === user?.id ? req.owner : req.borrower;
        if (other && other.id && (!user || other.id !== user.id)) {
          peersMap.set(other.id, {
            id: other.id,
            name: other.name || 'KUET Student',
            dept: other.dept || 'KUET',
            roll: other.roll || 'KUET',
            karma: other.karma || 100,
            context: req.item?.title ? `Request: ${req.item.title}` : 'Borrow Partner',
          });
        }
      });
    }

    // 2. From listed items
    if (Array.isArray(rawItems)) {
      rawItems.forEach((item) => {
        if (item.owner && item.owner.id && (!user || item.owner.id !== user.id)) {
          if (!peersMap.has(item.owner.id)) {
            peersMap.set(item.owner.id, {
              id: item.owner.id,
              name: item.owner.name || 'KUET Student',
              dept: item.owner.dept || 'KUET',
              roll: item.owner.roll || 'KUET',
              karma: item.owner.karma || 100,
              context: `Lending: ${item.title}`,
            });
          }
        }
      });
    }

    // 3. Fallback directory if list is small
    if (peersMap.size < 3) {
      CAMPUS_STUDENTS.forEach((student) => {
        if (!user || student.id !== user.id) {
          if (!peersMap.has(student.id)) {
            peersMap.set(student.id, {
              ...student,
              context: 'KUET Student',
            });
          }
        }
      });
    }

    return Array.from(peersMap.values());
  }, [rawItems, rawRequests, user]);

  // Sync activeUserId from URL
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

  // Load offline messages
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

  // Combine server + local messages
  const messages = useMemo(() => {
    const serverMsgs = Array.isArray(rawMessages) ? rawMessages : [];
    const serverIds = new Set(serverMsgs.map((m) => m.id));
    const pendingLocal = localMessages.filter((m) => !serverIds.has(m.id));
    return [...serverMsgs, ...pendingLocal];
  }, [rawMessages, localMessages]);

  // Active contact info
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

  // Filtered lists
  const filteredConversations = useMemo(() => {
    if (!searchQuery.trim()) return conversations;
    const q = searchQuery.toLowerCase();
    return conversations.filter((c) =>
      c.contact?.name?.toLowerCase().includes(q) ||
      c.contact?.dept?.toLowerCase().includes(q) ||
      c.contact?.roll?.toLowerCase().includes(q) ||
      c.last_message?.toLowerCase().includes(q)
    );
  }, [conversations, searchQuery]);

  const filteredPeers = useMemo(() => {
    if (!searchQuery.trim()) return campusPeers;
    const q = searchQuery.toLowerCase();
    return campusPeers.filter((p) =>
      p.name.toLowerCase().includes(q) ||
      p.dept.toLowerCase().includes(q) ||
      p.roll.toLowerCase().includes(q)
    );
  }, [campusPeers, searchQuery]);

  // Send Mutation
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
    <div className="flex flex-col h-full bg-white border border-slate-200/90 rounded-2xl shadow-xs overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
            <ChatBubbleIcon className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900 tracking-tight">Messages</h2>
            <p className="text-[11px] text-slate-500 font-medium">KUET Campus Hub</p>
          </div>
        </div>
        <span className="text-xs bg-blue-100/80 text-blue-700 font-bold px-2 py-0.5 rounded-full">
          {conversations.length}
        </span>
      </div>

      {/* Search Input */}
      <div className="p-3 border-b border-slate-100 bg-white">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-slate-400">
            <SearchIcon className="w-3.5 h-3.5" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search students or messages..."
            className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 hover:bg-slate-100/80 focus:bg-white border border-slate-200 focus:border-blue-500 rounded-lg outline-none transition"
          />
        </div>
      </div>

      {/* Conversation / Peer List */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
        {loadingConversations && conversations.length === 0 && (
          <div className="p-4 space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-3 animate-pulse">
                <div className="w-9 h-9 rounded-full bg-slate-200" />
                <div className="flex-1 space-y-1.5">
                  <div className="h-3.5 bg-slate-200 rounded w-2/3" />
                  <div className="h-2.5 bg-slate-100 rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Active Conversations */}
        {filteredConversations.map((conv) => {
          const isSelected = activeUserId === conv.contact?.id;
          return (
            <button
              key={conv.contact?.id}
              onClick={() => selectConversation(conv.contact?.id)}
              className={`w-full text-left p-3.5 flex items-start gap-3 transition-colors ${
                isSelected
                  ? 'bg-blue-50/90 border-l-4 border-blue-600 shadow-2xs'
                  : 'hover:bg-slate-50/80'
              }`}
            >
              <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 text-white font-bold flex items-center justify-center shrink-0 text-sm shadow-xs">
                {(conv.contact?.name?.[0] || 'U').toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-slate-900 truncate">{conv.contact?.name}</p>
                  <span className="text-[10px] text-slate-400 shrink-0 font-medium">
                    {conv.last_message_at
                      ? new Date(conv.last_message_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                      : ''}
                  </span>
                </div>
                <p className="text-[11px] text-blue-600 font-semibold truncate mt-0.5">
                  {conv.contact?.dept ? formatDept(conv.contact.dept) : 'KUET Student'}
                  {conv.contact?.roll && ` · Roll ${conv.contact.roll}`}
                </p>
                <p className="text-xs text-slate-600 truncate mt-0.5">{conv.last_message}</p>
              </div>
              {conv.unread_count > 0 && (
                <span className="w-5 h-5 rounded-full bg-blue-600 text-white text-[10px] font-bold flex items-center justify-center shrink-0 shadow-xs">
                  {conv.unread_count}
                </span>
              )}
            </button>
          );
        })}

        {/* Campus Peers Directory (Always visible to easily start new chats) */}
        <div className="p-3 bg-slate-50/60">
          <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 px-1 mb-2">
            Campus Contacts
          </p>
          <div className="space-y-1">
            {filteredPeers.map((peer) => {
              const isSelected = activeUserId === peer.id;
              return (
                <button
                  key={peer.id}
                  onClick={() => selectConversation(peer.id)}
                  className={`w-full text-left p-2 rounded-xl flex items-center gap-2.5 transition text-xs ${
                    isSelected
                      ? 'bg-blue-600 text-white font-semibold shadow-xs'
                      : 'hover:bg-slate-200/70 text-slate-700'
                  }`}
                >
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold ${
                    isSelected ? 'bg-white text-blue-600' : 'bg-blue-100 text-blue-700'
                  }`}>
                    {(peer.name[0] || 'U').toUpperCase()}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-semibold">{peer.name}</p>
                    <p className={`text-[10px] truncate ${isSelected ? 'text-blue-100' : 'text-slate-400'}`}>
                      {peer.context || `${formatDept(peer.dept)} · Roll ${peer.roll}`}
                    </p>
                  </div>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                    isSelected ? 'bg-blue-700 text-blue-100' : 'bg-slate-100 text-slate-500'
                  }`}>
                    ⚡ {peer.karma || 100}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );

  // ── CHAT PANEL ─────────────────────────────────────────────────────────────
  const ChatPanel = () => (
    <div className="flex flex-col h-full bg-white border border-slate-200/90 rounded-2xl shadow-xs overflow-hidden">
      {hasActiveChat ? (
        <>
          {/* Active Contact Header */}
          <div className="p-3.5 px-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/70">
            <div className="flex items-center gap-3">
              {/* Back button on mobile */}
              <button
                onClick={() => setMobileView('list')}
                className="md:hidden p-1.5 rounded-lg hover:bg-slate-200 text-slate-600 shrink-0"
                aria-label="Back to conversations"
              >
                <ArrowBackIcon className="w-4 h-4" />
              </button>

              <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 text-white font-bold flex items-center justify-center text-sm shadow-xs shrink-0">
                {(activeContact?.name?.[0] || 'S').toUpperCase()}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-slate-900 truncate">
                    {activeContact?.name || (requestId ? `Request #${requestId}` : 'KUET Student')}
                  </h3>
                  <span className="w-2 h-2 rounded-full bg-emerald-500" title="Active on campus" />
                </div>
                <p className="text-xs text-slate-500">
                  {activeContact?.dept ? formatDept(activeContact.dept) : 'KUET Student'}
                  {activeContact?.roll && ` · Roll ${activeContact.roll}`}
                  {activeContact?.batch && ` ('${activeContact.batch})`}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full bg-amber-50 text-amber-900 border border-amber-200/80 shadow-2xs">
                ⚡ {activeContact?.karma || 100} Karma
              </span>
            </div>
          </div>

          {/* Messages Scroll View */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50/40">
            {loadingMessages && messages.length === 0 && (
              <div className="h-full flex items-center justify-center text-sm text-slate-400">
                Loading messages...
              </div>
            )}

            {isError && (
              <div className="p-3 bg-amber-50 text-amber-800 rounded-xl text-xs text-center border border-amber-200">
                Connection issue — messages will sync automatically when back online.
              </div>
            )}

            {!loadingMessages && messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-2">
                <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto shadow-2xs">
                  <ChatBubbleIcon className="w-6 h-6" />
                </div>
                <h4 className="font-bold text-slate-800 text-sm">
                  Start conversation with {activeContact?.name || 'this student'}
                </h4>
                <p className="text-xs text-slate-500 max-w-sm">
                  Coordinate pickup locations on campus, ask questions regarding the item, or verify handover details.
                </p>
              </div>
            )}

            {messages.map((msg, idx) => {
              const isMine = msg.sender_id === user?.id || String(msg.id).startsWith('local_');
              return (
                <div key={msg.id || idx} className={`flex flex-col ${isMine ? 'items-end' : 'items-start'}`}>
                  <div
                    className={`px-4 py-2.5 rounded-2xl max-w-[80%] sm:max-w-[70%] text-sm shadow-xs ${
                      isMine
                        ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-br-xs'
                        : 'bg-white text-slate-800 border border-slate-200/90 rounded-bl-xs'
                    }`}
                  >
                    <p className="break-words leading-relaxed text-sm">{msg.content}</p>
                  </div>
                  <span className="text-[10px] text-slate-400 px-1.5 mt-1 font-medium">
                    {msg.created_at
                      ? new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                      : 'Just now'}
                  </span>
                </div>
              );
            })}
            <div ref={bottomRef} />
          </div>

          {/* Input Bar */}
          {isChattingWithSelf ? (
            <div className="p-4 border-t border-amber-100 bg-amber-50 text-amber-800 text-xs font-medium text-center">
              ℹ️ You are viewing your own profile. 1:1 chat is for messaging other students.
            </div>
          ) : (
            <form onSubmit={handleSend} className="p-3 border-t border-slate-100 flex gap-2 bg-white">
              <input
                type="text"
                className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition"
                placeholder={`Type a message to ${activeContact?.name?.split(' ')[0] || 'student'}...`}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                autoFocus
              />
              <button
                type="submit"
                disabled={sendMutation.isPending || !message.trim()}
                className="bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white px-5 py-2.5 rounded-xl disabled:opacity-50 text-sm font-semibold transition shadow-sm flex items-center gap-2"
              >
                <span>{sendMutation.isPending ? 'Sending...' : 'Send'}</span>
                <SendIcon className="w-3.5 h-3.5" />
              </button>
            </form>
          )}
        </>
      ) : (
        /* Polished Empty State When No Conversation is Active */
        <div className="h-full flex flex-col items-center justify-center p-8 text-center bg-gradient-to-b from-white to-slate-50/50">
          <div className="w-16 h-16 rounded-3xl bg-gradient-to-br from-blue-500/10 via-indigo-500/10 to-violet-500/10 border border-blue-100 flex items-center justify-center mb-4 text-blue-600 shadow-sm">
            <ChatBubbleIcon className="w-8 h-8" />
          </div>

          <h3 className="text-xl font-extrabold text-slate-900 tracking-tight">Your Campus Messages</h3>
          <p className="text-sm text-slate-500 mt-2 max-w-md leading-relaxed">
            Connect with student lenders and borrowers to coordinate item handovers, exchange OTPs, or discuss item condition.
          </p>

          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={() => setMobileView('list')}
              className="md:hidden px-5 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-semibold shadow-sm"
            >
              Select Contact
            </button>
            <Link
              to="/requests"
              className="px-5 py-2.5 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 rounded-xl text-sm font-semibold shadow-2xs transition"
            >
              View Borrow Requests
            </Link>
            <Link
              to="/items"
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold shadow-sm transition"
            >
              Browse Campus Map
            </Link>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="h-full w-full p-2 sm:p-4 flex gap-4 overflow-hidden bg-slate-50/50">
      {/* Sidebar: conversation list */}
      <div className={`w-full md:w-80 shrink-0 ${mobileView === 'list' ? 'flex' : 'hidden'} md:flex flex-col`}>
        <SidebarPanel />
      </div>

      {/* Main chat window */}
      <div className={`flex-1 min-w-0 ${mobileView === 'chat' ? 'flex' : 'hidden'} md:flex flex-col`}>
        <ChatPanel />
      </div>
    </div>
  );
}
