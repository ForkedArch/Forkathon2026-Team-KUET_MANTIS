import React, { useState, useMemo } from 'react';
import { Routes, Route, Navigate, useNavigate, Link } from 'react-router-dom';
import { Toaster, toast } from 'react-hot-toast';
import { useAuth } from './context/AuthContext';
import DashboardLayout from './components/layout/DashboardLayout';
import Home from './pages/Home';
import AllItems from './pages/AllItems';
import AddItem from './pages/AddItem';
import ItemDetail from './pages/ItemDetail';
import Requests from './pages/Requests';
import Chat from './pages/Chat';
import Transaction from './pages/Transaction';
import Profile from './pages/Profile';
import api from './api/client';
import { KUET_DEPTS, formatDept } from './utils/dept';
import Logo from './components/common/Logo';
import { KarmaIcon } from './components/common/KarmaIcon';

/**
 * KUET Email & Roll Decoder
 */
export function decodeKuetEmail(email) {
  const clean = (email || '').trim().toLowerCase();
  if (!clean) return { status: 'empty' };

  if (!clean.includes('@')) {
    return { status: 'typing' };
  }

  if (!clean.endsWith('@stud.kuet.ac.bd')) {
    return {
      status: 'invalid_domain',
      message: 'Only official @stud.kuet.ac.bd student emails are accepted.'
    };
  }

  const localPart = clean.split('@')[0];
  const match = localPart.match(/(\d{2})(\d{2})(\d{3})$/);
  if (!match) {
    return {
      status: 'invalid_format',
      message: 'Email must end with 7-digit student ID (e.g., siddique2307010@stud.kuet.ac.bd).'
    };
  }

  const [, batchDigits, deptDigits, rollDigits] = match;
  const deptInfo = KUET_DEPTS[deptDigits] || {
    code: `Dept ${deptDigits}`,
    name: `Department ${deptDigits}`
  };

  return {
    status: 'valid',
    batch: batchDigits,
    batchYear: `20${batchDigits}`,
    deptCode: deptInfo.code,
    deptName: deptInfo.name,
    roll: rollDigits,
    fullRoll: `${batchDigits}${deptDigits}${rollDigits}`,
    startingKarma: 100
  };
}

// Standalone Login Component
function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success('Welcome back to CampusShare KUET!');
      navigate('/');
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Login failed';
      toast.error(msg, { duration: 6000 });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4 font-sans">
      <div className="w-full max-w-md bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
        <div className="flex items-center gap-3.5 mb-6">
          <Logo size="lg" />
          <div>
            <h1 className="text-xl font-bold text-slate-900">CampusShare KUET</h1>
            <p className="text-xs text-slate-500">Sign in to your student account</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">KUET Email</label>
            <input
              type="email"
              placeholder="e.g. siddique2307010@stud.kuet.ac.bd"
              className="w-full text-sm border border-slate-200 rounded-lg px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
            <input
              type="password"
              placeholder="••••••••"
              className="w-full text-sm border border-slate-200 rounded-lg px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold rounded-lg shadow-sm transition-colors text-sm disabled:opacity-50"
          >
            {loading ? 'Connecting to server...' : 'Sign In'}
          </button>
        </form>

        <p className="mt-5 text-center text-xs text-slate-500">
          Don't have an account?{' '}
          <Link to="/register" className="font-semibold text-blue-600 hover:underline">
            Register with KUET email
          </Link>
        </p>
      </div>
    </div>
  );
}

// Standalone Register Component (R3 minimal 3 fields: name, email, password)
function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // Automatic Roll Decoder preview
  const decoded = useMemo(() => decodeKuetEmail(email), [email]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (decoded.status !== 'valid') {
      toast.error(decoded.message || 'Please provide a valid @stud.kuet.ac.bd student email');
      return;
    }

    setLoading(true);
    try {
      // Sends strictly 3 fields as mandated by R3
      await api.post('/auth/register', {
        name: name.trim(),
        email: email.trim().toLowerCase(),
        password
      });
      toast.success('Registration successful! 100 Base Karma awarded. ⚡');
      navigate('/login');
    } catch (err) {
      toast.error(err.response?.data?.detail || err.message || 'Registration failed', { duration: 6000 });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4 font-sans">
      <div className="w-full max-w-md bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
        <div className="flex items-center gap-3.5 mb-6">
          <Logo size="lg" />
          <div>
            <h1 className="text-xl font-bold text-slate-900">Student Registration</h1>
            <p className="text-xs text-slate-500">Auto-decodes Batch, Dept & Roll with 100 Base Karma</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Field 1: Full Name */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name *</label>
            <input
              type="text"
              placeholder="e.g. Siddique Ahmed"
              className="w-full text-sm border border-slate-200 rounded-lg px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          {/* Field 2: KUET Student Email */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              KUET Student Email (@stud.kuet.ac.bd) *
            </label>
            <input
              type="email"
              placeholder="siddique2307010@stud.kuet.ac.bd"
              className="w-full text-sm border border-slate-200 rounded-lg px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            
            {/* Live Roll Decoder Badge */}
            {decoded.status === 'valid' && (
              <div className="mt-2.5 p-3 bg-blue-50 border border-blue-200 rounded-xl space-y-1 text-xs text-blue-900 animate-fade-in shadow-xs">
                <div className="flex items-center justify-between font-bold text-blue-800">
                  <span className="flex items-center gap-1.5">
                    <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path d="M12 14l9-5-9-5-9 5 9 5z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                      <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <span>KUET Credentials Decoded</span>
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                    <KarmaIcon className="w-3 h-3 text-amber-600" />
                    <span>100 Base Karma</span>
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 pt-1 text-center font-medium">
                  <div className="bg-white/80 rounded-lg p-1 border border-blue-100">
                    <span className="text-[10px] text-slate-500 block">Batch</span>
                    <span className="font-bold text-slate-800">{decoded.batchYear} ('{decoded.batch})</span>
                  </div>
                  <div className="bg-white/80 rounded-lg p-1 border border-blue-100">
                    <span className="text-[10px] text-slate-500 block">Dept</span>
                    <span className="font-bold text-slate-800" title={decoded.deptName}>{decoded.deptCode}</span>
                  </div>
                  <div className="bg-white/80 rounded-lg p-1 border border-blue-100">
                    <span className="text-[10px] text-slate-500 block">Roll</span>
                    <span className="font-bold text-slate-800">{decoded.roll}</span>
                  </div>
                </div>
              </div>
            )}

            {decoded.status === 'invalid_domain' && (
              <div className="mt-2 p-2 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex items-center gap-1.5">
                <svg className="w-4 h-4 shrink-0 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span>{decoded.message}</span>
              </div>
            )}

            {decoded.status === 'invalid_format' && (
              <div className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-center gap-1.5">
                <svg className="w-4 h-4 shrink-0 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{decoded.message}</span>
              </div>
            )}
          </div>

          {/* Field 3: Password */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Password *</label>
            <input
              type="password"
              placeholder="••••••••"
              className="w-full text-sm border border-slate-200 rounded-lg px-3.5 py-2.5 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <span className="text-[10px] text-slate-500 mt-1 block">
              Department, Batch, and Roll will be inferred automatically from your email.
            </span>
          </div>

          <button
            type="submit"
            disabled={loading || decoded.status !== 'valid'}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-sm transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
          >
            <span>{loading ? 'Registering...' : 'Register & Claim 100 Base Karma'}</span>
            {!loading && <KarmaIcon className="w-3.5 h-3.5 text-amber-300" />}
          </button>
        </form>

        <p className="mt-5 text-center text-xs text-slate-500">
          Already registered?{' '}
          <Link to="/login" className="font-semibold text-blue-600 hover:underline">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}

// Private route guard
function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-center text-slate-500">Loading student session...</div>;
  return user ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <>
      <Toaster position="top-center" toastOptions={{ duration: 3500 }} />
      <Routes>
        {/* Standalone Authentication Views */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Enterprise Dashboard Shell Layout */}
        <Route element={<DashboardLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/items" element={<AllItems />} />
          <Route path="/item/:id" element={<ItemDetail />} />
          <Route path="/add" element={<PrivateRoute><AddItem /></PrivateRoute>} />
          <Route path="/requests" element={<PrivateRoute><Requests /></PrivateRoute>} />
          <Route path="/chat" element={<PrivateRoute><Chat /></PrivateRoute>} />
          <Route path="/chat/:requestId" element={<PrivateRoute><Chat /></PrivateRoute>} />
          <Route path="/transaction/:requestId" element={<PrivateRoute><Transaction /></PrivateRoute>} />
          <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
        </Route>
      </Routes>
    </>
  );
}
