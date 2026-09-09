import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-white shadow-md px-6 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <Link to="/" className="text-xl font-bold text-blue-600">CampusShare</Link>
        <span className="text-sm text-gray-500">KUET</span>
      </div>
      <div className="flex items-center space-x-4">
        {user ? (
          <>
            <Link to="/add" className="text-blue-600 hover:underline">+ Add Item</Link>
            <Link to="/requests" className="hover:underline">Requests</Link>
            <Link to="/profile" className="hover:underline">{user.name}</Link>
            <button onClick={handleLogout} className="text-red-500 hover:underline">Logout</button>
          </>
        ) : (
          <>
            <Link to="/login" className="hover:underline">Login</Link>
            <Link to="/register" className="hover:underline">Register</Link>
          </>
        )}
      </div>
    </nav>
  );
}