import React, { useState } from 'react';
import { API_ORIGIN } from '../../api/client';
import { formatDept } from '../../utils/dept';
import { KarmaIcon } from '../common/KarmaIcon';

/**
 * ItemHoverCard
 * 
 * Reusable modern popover/hover card for items.
 * Displays item specs, mini-location, owner info, KUET Karma rating,
 * and inline quick actions ("Request to Borrow", "Chat").
 */
export default function ItemHoverCard({
  item,
  onRequest,
  onChat,
  onFocusOnMap,
  variant = 'card'
}) {
  const [isHovered, setIsHovered] = useState(false);

  // Formatting Fallbacks
  const placeholderImage = 'https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=500&auto=format&fit=crop&q=60';
  const rawImage = item.image_url || item.image;
  const imageSrc = rawImage
    ? (rawImage.startsWith('http') ? rawImage : `${API_ORIGIN}${rawImage}`)
    : placeholderImage;

  const isBeacon = item.type === 'borrow';
  const ownerName = item.owner?.name || item.lender_name || 'KUET Student';
  const ownerDept = formatDept(item.owner?.dept || item.dept) || 'KUET';
  const ownerRoll = item.owner?.roll || item.roll || 'Verified';
  const ownerKarma = item.owner?.karma ?? item.karma ?? 100;
  const totalExchanges = (item.owner?.total_lends || 0) + (item.owner?.total_borrows || 0) || item.total_exchanges || 12;

  // Initials for avatar
  const initials = ownerName
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map(w => w[0])
    .join('')
    .toUpperCase() || 'KU';

  // Coordinates & Landmark
  const lat = item.latitude ?? item.lat;
  const lng = item.longitude ?? item.lng;
  const hasCoords = lat !== null && lat !== undefined && lng !== null && lng !== undefined;
  const zoneName = item.zone || item.zone_id || 'KUET Main Campus';

  return (
    <div
      className="relative group bg-white rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-xl transition-all duration-200 overflow-hidden flex flex-col"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* 1. Thumbnail Header with Status Badges */}
      <div className="relative w-full h-44 bg-slate-100 overflow-hidden">
        <img
          src={imageSrc}
          alt={item.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          onError={(e) => { e.target.src = placeholderImage; }}
        />
        
        {/* Type Badge (Lend vs Borrow Beacon) */}
        <div className="absolute top-3 left-3">
          {isBeacon ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-600/90 text-white backdrop-blur-md shadow-md animate-pulse">
              <span className="h-2 w-2 rounded-full bg-white"></span>
              Demand Beacon
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-600/90 text-white backdrop-blur-md shadow-md">
              <span className="h-2 w-2 rounded-full bg-emerald-200"></span>
              Available to Lend
            </span>
          )}
        </div>

        {/* Condition Badge */}
        <div className="absolute top-3 right-3">
          <span className="px-2 py-0.5 rounded-md text-[11px] font-semibold bg-white/90 text-slate-700 backdrop-blur-md shadow-sm border border-slate-200/50">
            {item.condition || 'Good'}
          </span>
        </div>

        {/* Category Pill Over Image Bottom */}
        <div className="absolute bottom-2.5 left-3">
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-900/75 text-white backdrop-blur-sm">
            {item.category || 'General'}
          </span>
        </div>
      </div>

      {/* 2. Content Body */}
      <div className="p-4 flex-1 flex flex-col justify-between">
        <div>
          {/* Title */}
          <h3 className="text-base font-bold text-slate-900 truncate mb-1" title={item.title}>
            {item.title}
          </h3>

          {/* Description / Specs */}
          <p className="text-xs text-slate-600 line-clamp-2 mb-3">
            {item.specs || item.description || 'No additional specifications provided.'}
          </p>

          {/* 3. Mini-Location Badge */}
          <div className="bg-slate-50 border border-slate-200/70 rounded-xl p-2.5 mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2 min-w-0">
              <svg className="w-4 h-4 text-blue-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <div className="min-w-0">
                <div className="text-xs font-semibold text-slate-800 truncate">{zoneName}</div>
                <div className="text-[10px] text-slate-500 truncate">
                  {hasCoords ? `${Number(lat).toFixed(4)}°N, ${Number(lng).toFixed(4)}°E` : 'Campus perimeter'} · Within 700m
                </div>
              </div>
            </div>
            {hasCoords && onFocusOnMap && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onFocusOnMap([Number(lng), Number(lat)]);
                }}
                className="flex-shrink-0 ml-2 px-2 py-1 text-[11px] font-medium text-blue-700 hover:text-blue-800 bg-blue-50 hover:bg-blue-100 rounded-lg transition flex items-center gap-1"
                title="Pan map to this location"
              >
                <svg className="w-3 h-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z" />
                </svg>
                <span>Focus</span>
              </button>
            )}
          </div>

          {/* 4. Owner Info & KUET Karma Rating Badge */}
          <div className="flex items-center justify-between pt-2 border-t border-slate-100">
            {/* Student Details */}
            <div className="flex items-center gap-2 min-w-0">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-600 to-indigo-600 text-white font-bold text-xs flex items-center justify-center shadow-sm flex-shrink-0">
                {initials}
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold text-slate-900 truncate flex items-center gap-1">
                  {ownerName}
                  <span className="text-blue-600 text-[10px]" title="Verified KUET Student">✓</span>
                </div>
                <div className="text-[10px] text-slate-500 truncate">
                  {ownerDept} · Roll {ownerRoll}
                </div>
              </div>
            </div>

            {/* KUET Karma Score Pill */}
            <div className="flex flex-col items-end flex-shrink-0">
              <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-900 border border-amber-200 shadow-2xs">
                <KarmaIcon className="w-3 h-3 text-amber-500" />
                <span>{ownerKarma}</span>
                <span className="text-[10px] font-medium text-amber-700">Karma</span>
              </div>
              <span className="text-[9px] text-slate-600 mt-0.5">
                {totalExchanges} exchanges
              </span>
            </div>
          </div>
        </div>

        {/* 5. Quick Actions (Inline Modal Trigger, Avoiding Page Redirects) */}
        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-2">
          {onRequest && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onRequest(item);
              }}
              className={`flex-1 py-2 px-3 rounded-xl text-xs font-semibold shadow-sm transition flex items-center justify-center gap-1.5 ${
                isBeacon
                  ? 'bg-amber-600 hover:bg-amber-700 text-white'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {isBeacon ? (
                <>
                  <KarmaIcon className="w-3.5 h-3.5 text-white" />
                  <span>Offer to Lend</span>
                </>
              ) : (
                <span>Request to Borrow</span>
              )}
            </button>
          )}

          {onChat && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onChat(item.owner || { name: ownerName });
              }}
              className="px-3 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-semibold transition flex items-center justify-center"
              title="Chat with owner"
            >
              <svg className="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
