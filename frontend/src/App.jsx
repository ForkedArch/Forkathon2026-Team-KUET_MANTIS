import { useState } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useAuth } from './context/AuthContext';
import Navbar from './components/common/Navbar';
import Home from './pages/Home';
import AddItem from './pages/AddItem';
import ItemDetail from './pages/ItemDetail';
import Requests from './pages/Requests';
import Chat from './pages/Chat';
import Transaction from './pages/Transaction';
import Profile from './pages/Profile';
import api from './api/client';

// Simple login/register pages inline for brevity
function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      alert(err.response?.data?.detail || 'Login failed');
    }
  };

  return (
    <div className="max-w-md mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Login</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input type="email" placeholder="Email" className="w-full border rounded px-3 py-2" value={email} onChange={e => setEmail(e.target.value)} required />
        <input type="password" placeholder="Password" className="w-full border rounded px-3 py-2" value={password} onChange={e => setPassword(e.target.value)} required />
        <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded">Login</button>
      </form>
    </div>
  );
}

function Register() {
  const [form, setForm] = useState({ email: '', name: '', dept: '', batch: '', roll: '', password: '' });
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/auth/register', form);
      alert('Registration successful! Please login.');
      navigate('/login');
    } catch (err) {
      alert(err.response?.data?.detail || 'Registration failed');
    }
  };

  return (
    <div className="max-w-md mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Register</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input type="email" placeholder="KUET Email" className="w-full border rounded px-3 py-2" value={form.email} onChange={e => setForm({...form, email: e.target.value})} required />
        <input type="text" placeholder="Full Name" className="w-full border rounded px-3 py-2" value={form.name} onChange={e => setForm({...form, name: e.target.value})} required />
        <input type="text" placeholder="Department (e.g. CSE)" className="w-full border rounded px-3 py-2" value={form.dept} onChange={e => setForm({...form, dept: e.target.value})} required />
        <input type="text" placeholder="Batch (e.g. 2022)" className="w-full border rounded px-3 py-2" value={form.batch} onChange={e => setForm({...form, batch: e.target.value})} required />
        <input type="text" placeholder="Roll Number" className="w-full border rounded px-3 py-2" value={form.roll} onChange={e => setForm({...form, roll: e.target.value})} required />
        <input type="password" placeholder="Password" className="w-full border rounded px-3 py-2" value={form.password} onChange={e => setForm({...form, password: e.target.value})} required />
        <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded">Register</button>
      </form>
    </div>
  );
}

// Private route wrapper
function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div>Loading...</div>;
  return user ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <Toaster position="top-center" />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/item/:id" element={<ItemDetail />} />
        <Route path="/add" element={<PrivateRoute><AddItem /></PrivateRoute>} />
        <Route path="/requests" element={<PrivateRoute><Requests /></PrivateRoute>} />
        <Route path="/chat/:requestId" element={<PrivateRoute><Chat /></PrivateRoute>} />
        <Route path="/transaction/:requestId" element={<PrivateRoute><Transaction /></PrivateRoute>} />
        <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
      </Routes>
    </div>
  );
}