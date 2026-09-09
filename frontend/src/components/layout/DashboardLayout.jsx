import React, { useState, useEffect, createContext, useContext } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import Sidebar from './Sidebar';
import TopActionBar from './TopActionBar';
import AddItemModal from '../items/AddItemModal';
import RequestModal from '../requests/RequestModal';
import api from '../../api/client';
import { useAuth } from '../../context/AuthContext';

const DashboardContext = createContext(null);

export const useDashboard = () => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error('useDashboard must be used within a DashboardLayout');
  }
  return context;
};

export default function DashboardLayout() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('ALL');
  const [listingType, setListingType] = useState('ALL'); // 'ALL' | 'lend' | 'borrow'

  // Modal states
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isPinMode, setIsPinMode] = useState(false);
  const [pinpointCoords, setPinpointCoords] = useState(null);

  const [requestModalItem, setRequestModalItem] = useState(null);

  // Fetch campus landmarks
  const { data: landmarksData } = useQuery({
    queryKey: ['landmarks'],
    queryFn: () => api.get('/landmarks').then(res => res.data).catch(() => ({ zones: [] })),
    staleTime: 1000 * 60 * 30
  });
  const landmarks = landmarksData?.zones || [];

  // Handle CTA button click
  const handleOpenAdd = () => {
    if (!user) {
      navigate('/login');
      return;
    }
    setIsAddModalOpen(true);
  };

  // Trigger pinpoint mode from inside AddItemModal
  const handleStartPinpoint = () => {
    setIsAddModalOpen(false);
    setIsPinMode(true);
    // If not already on home map, navigate to /
    if (window.location.pathname !== '/') {
      navigate('/');
    }
  };

  // When user clicks map in pin mode
  const handleSelectLocation = (coords) => {
    setPinpointCoords(coords);
    setIsPinMode(false);
    setIsAddModalOpen(true);
  };

  const handleCancelPinMode = () => {
    setIsPinMode(false);
    setIsAddModalOpen(true);
  };

  // Trigger borrow request modal
  const handleOpenBorrowRequest = (item) => {
    if (!user) {
      navigate('/login');
      return;
    }
    setRequestModalItem(item);
  };

  // Set up global bridge for MapLibre popups
  useEffect(() => {
    window.__campusShareActions = {
      onRequestBorrow: (itemOrId) => {
        if (typeof itemOrId === 'object') {
          handleOpenBorrowRequest(itemOrId);
        } else {
          // fetch or find
          api.get(`/items/${itemOrId}`).then(res => handleOpenBorrowRequest(res.data)).catch(() => {});
        }
      },
      onChatUser: (username) => {
        navigate('/requests');
      }
    };
    return () => {
      delete window.__campusShareActions;
    };
  }, [user]);

  // Trigger window resize when sidebar state changes to adjust MapLibre canvas
  useEffect(() => {
    const timer = setTimeout(() => {
      window.dispatchEvent(new Event('resize'));
    }, 250);
    return () => clearTimeout(timer);
  }, [sidebarOpen]);

  const dashboardValue = {
    search,
    setSearch,
    category,
    setCategory,
    listingType,
    setListingType,
    isAddModalOpen,
    setIsAddModalOpen,
    isPinMode,
    setIsPinMode,
    pinpointCoords,
    setPinpointCoords,
    onOpenAddModal: handleOpenAdd,
    onStartPinpoint: handleStartPinpoint,
    onSelectLocation: handleSelectLocation,
    onCancelPinMode: handleCancelPinMode,
    onRequestBorrow: handleOpenBorrowRequest,
    landmarks
  };

  return (
    <DashboardContext.Provider value={dashboardValue}>
      <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans text-slate-900">
        {/* Left Sidebar Navigation */}
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        {/* Main Content Workspace */}
        <div className="flex flex-1 flex-col min-w-0 h-full overflow-hidden">
          {/* Top Action Bar */}
          <TopActionBar
            search={search}
            setSearch={setSearch}
            category={category}
            setCategory={setCategory}
            listingType={listingType}
            setListingType={setListingType}
            onOpenAddModal={handleOpenAdd}
            onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          />

          {/* Child Views (Map View, Items, Requests, Profile) */}
          <main className="relative flex-1 overflow-hidden bg-slate-50">
            <Outlet context={dashboardValue} />
          </main>
        </div>

        {/* Add Item Modal */}
        <AddItemModal
          isOpen={isAddModalOpen}
          onClose={() => setIsAddModalOpen(false)}
          onStartPinpoint={handleStartPinpoint}
          pinpointCoords={pinpointCoords}
          landmarks={landmarks}
        />

        {/* Request to Borrow Modal */}
        {requestModalItem && (
          <RequestModal
            itemId={requestModalItem.id}
            onClose={() => setRequestModalItem(null)}
          />
        )}
      </div>
    </DashboardContext.Provider>
  );
}
