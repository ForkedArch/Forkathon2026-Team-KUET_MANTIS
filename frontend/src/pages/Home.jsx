import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../api/client';
import GodsEyeMap from '../components/map/GodsEyeMap';
import { useDashboard } from '../components/layout/DashboardLayout';

export default function Home() {
  const {
    search,
    category,
    listingType,
    isPinMode,
    onSelectLocation,
    onCancelPinMode,
    onRequestBorrow
  } = useDashboard();

  const [selectedItemId, setSelectedItemId] = useState(null);

  const { data: items = [], isLoading } = useQuery({
    queryKey: ['items', { category, search, listingType }],
    queryFn: async () => {
      const params = {};
      if (search && search.trim() !== '') params.search = search.trim();
      if (category && category !== 'ALL') params.category = category;
      if (listingType && listingType !== 'ALL') params.type = listingType;
      const res = await api.get('/items', { params });
      return res.data;
    }
  });

  return (
    <div className="relative w-full h-full overflow-hidden flex flex-col">
      {/* MapLibre Canvas Viewport */}
      <div className="flex-1 w-full h-full relative">
        <GodsEyeMap
          items={items}
          selectedItemId={selectedItemId}
          isPinMode={isPinMode}
          onSelectLocation={onSelectLocation}
          onCancelPinMode={onCancelPinMode}
          onSelectItem={(item) => setSelectedItemId(item.id)}
          onRequestBorrow={onRequestBorrow}
          activeTypeFilter={listingType}
          activeCategoryFilter={category}
          searchQuery={search}
          className="w-full h-full"
        />

        {/* Floating Quick Stats Pill (Top-Left under header) */}
        <div className="absolute top-4 left-4 z-10 hidden sm:flex items-center gap-2 bg-white/90 backdrop-blur-md px-3.5 py-1.5 rounded-full border border-slate-200/80 shadow-sm text-xs text-slate-700">
          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span className="font-semibold">
            {isLoading ? 'Scanning campus...' : `${items.length} Active Items on KUET Map`}
          </span>
        </div>
      </div>
    </div>
  );
}
