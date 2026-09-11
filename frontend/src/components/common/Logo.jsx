import React from 'react';

/**
 * Modern CampusShare KUET Brand Logo
 * Represents reciprocal peer-to-peer campus sharing & trust network
 */
export default function Logo({ size = 'md', className = '', showText = false, textClassName = '' }) {
  const sizeMap = {
    xs: { box: 'w-7 h-7', svg: 'w-4 h-4', text: 'text-sm' },
    sm: { box: 'w-8 h-8', svg: 'w-5 h-5', text: 'text-base' },
    md: { box: 'w-10 h-10', svg: 'w-6 h-6', text: 'text-lg' },
    lg: { box: 'w-12 h-12', svg: 'w-7 h-7', text: 'text-xl' },
    xl: { box: 'w-16 h-16', svg: 'w-9 h-9', text: 'text-2xl' },
  };

  const currentSize = sizeMap[size] || sizeMap.md;

  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      {/* Visual Logo Mark */}
      <div
        className={`${currentSize.box} rounded-xl bg-gradient-to-br from-blue-600 via-indigo-600 to-violet-700 flex items-center justify-center shadow-md shadow-blue-600/25 ring-1 ring-white/30 flex-shrink-0 transition-transform hover:scale-105`}
      >
        <svg
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className={`${currentSize.svg} text-white`}
        >
          <defs>
            <linearGradient id="logo-grad-a" x1="6" y1="8" x2="26" y2="24" gradientUnits="userSpaceOnUse">
              <stop stopColor="#93C5FD" />
              <stop offset="1" stopColor="#FFFFFF" />
            </linearGradient>
            <linearGradient id="logo-grad-b" x1="26" y1="24" x2="6" y2="8" gradientUnits="userSpaceOnUse">
              <stop stopColor="#FCD34D" />
              <stop offset="1" stopColor="#FFFFFF" />
            </linearGradient>
          </defs>

          {/* Interlocking dynamic exchange arcs (Sharing & Karma loops) */}
          {/* Top-Right Arc with Arrow */}
          <path
            d="M12 9H21C23.7614 9 26 11.2386 26 14C26 16.7614 23.7614 19 21 19H19"
            stroke="url(#logo-grad-a)"
            strokeWidth="2.75"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M15 6L11.5 9L15 12"
            stroke="url(#logo-grad-a)"
            strokeWidth="2.75"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Bottom-Left Arc with Arrow */}
          <path
            d="M20 23H11C8.23858 23 6 20.7614 6 18C6 15.2386 8.23858 13 11 13H13"
            stroke="url(#logo-grad-b)"
            strokeWidth="2.75"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M17 26L20.5 23L17 20"
            stroke="url(#logo-grad-b)"
            strokeWidth="2.75"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Center Trust / Spark Core */}
          <circle cx="16" cy="16" r="2.25" fill="#FFFFFF" />
        </svg>
      </div>

      {/* Optional Brand Text */}
      {showText && (
        <div>
          <div className="flex items-center gap-1.5">
            <span className={`font-bold tracking-tight text-slate-900 ${currentSize.text} ${textClassName}`}>
              CampusShare
            </span>
            <span className="text-[10px] font-extrabold bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded tracking-wide">
              KUET
            </span>
          </div>
          <p className="text-[11px] text-slate-500 font-medium">Peer-to-Peer Campus Hub</p>
        </div>
      )}
    </div>
  );
}
