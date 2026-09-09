import { useAuth } from '../context/AuthContext';

export default function Profile() {
  const { user } = useAuth();
  if (!user) return <div>Please login</div>;

  return (
    <div className="max-w-lg mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Profile</h1>
      <div className="bg-white shadow rounded p-6">
        <p><strong>Name:</strong> {user.name}</p>
        <p><strong>Email:</strong> {user.email}</p>
        <p><strong>Department:</strong> {user.dept}</p>
        <p><strong>Batch:</strong> {user.batch}</p>
        <p><strong>Roll:</strong> {user.roll}</p>
        <p><strong>Trust Score:</strong> ⭐ {user.trust_score?.toFixed(1) || 4.5}</p>
        <p><strong>Total Lends:</strong> {user.total_lends}</p>
        <p><strong>Total Borrows:</strong> {user.total_borrows}</p>
      </div>
    </div>
  );
}