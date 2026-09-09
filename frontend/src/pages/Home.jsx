import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import api from '../api/client';
import ItemCard from '../components/items/ItemCard';
import Loader from '../components/common/Loader';

export default function Home() {
  const [category, setCategory] = useState('');
  const [search, setSearch] = useState('');

  const { data: items, isLoading, error } = useQuery({
    queryKey: ['items', { category, search }],
    queryFn: () => api.get('/items', { params: { category, search } }).then(res => res.data)
  });

  if (isLoading) return <Loader />;
  if (error) return <div className="text-red-500">Failed to load items</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Available Items</h1>
      <div className="flex flex-wrap gap-4 mb-6">
        <input
          type="text"
          placeholder="Search..."
          className="border rounded px-4 py-2 flex-1"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="border rounded px-4 py-2"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">All Categories</option>
          <option value="Calculators">Calculators</option>
          <option value="Chargers">Chargers</option>
          <option value="Books">Books</option>
          <option value="Lab Equipment">Lab Equipment</option>
          <option value="Others">Others</option>
        </select>
      </div>
      {items?.length === 0 ? (
        <p>No items available.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {items?.map(item => <ItemCard key={item.id} item={item} />)}
        </div>
      )}
    </div>
  );
}