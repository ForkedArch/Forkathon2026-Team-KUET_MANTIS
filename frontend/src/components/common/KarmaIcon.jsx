import React from 'react';

/**
 * Modern Karma Spark Icon and Badge
 * Replaces the raw emoji ⚡ with a clean vector energy spark.
 */
export const KarmaIcon = ({ className = "w-3.5 h-3.5 text-amber-500" }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 20 20">
    <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
  </svg>
);

export const KarmaBadge = ({ karma = 100, className = "" }) => (
  <span className={`inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-900 border border-amber-200/80 shadow-2xs ${className}`}>
    <KarmaIcon className="w-3.5 h-3.5 text-amber-500" />
    <span>{karma} Karma</span>
  </span>
);

export default KarmaIcon;
