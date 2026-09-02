import React from 'react';

interface BrandLogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  className?: string;
}

export default function BrandLogo({
  size = 'md',
  showText = true,
  className = '',
}: BrandLogoProps) {
  const sizeConfig = {
    sm: {
      iconBox: 'h-8 w-8 rounded-lg',
      svg: 'h-4 w-4',
      text: 'text-lg',
      subText: 'text-[9px]',
    },
    md: {
      iconBox: 'h-9 w-9 rounded-xl',
      svg: 'h-5 w-5',
      text: 'text-xl',
      subText: 'text-[10px]',
    },
    lg: {
      iconBox: 'h-11 w-11 rounded-xl',
      svg: 'h-6 w-6',
      text: 'text-2xl',
      subText: 'text-xs',
    },
    xl: {
      iconBox: 'h-14 w-14 rounded-2xl',
      svg: 'h-8 w-8',
      text: 'text-3xl',
      subText: 'text-xs',
    },
  }[size];

  return (
    <div className={`inline-flex items-center gap-2.5 select-none ${className}`}>
      {/* ── Brand Emblem ── */}
      <div
        className={`relative flex shrink-0 items-center justify-center bg-gradient-to-br from-blue-600 via-indigo-600 to-sky-500 shadow-md shadow-blue-500/20 ring-1 ring-white/20 transition-transform duration-200 group-hover:scale-105 ${sizeConfig.iconBox}`}
      >
        <svg
          className={`${sizeConfig.svg} text-white drop-shadow-sm`}
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          {/* Stylized Modern Razor/Lightning Shopping Mark */}
          <path
            d="M3 4H5.5L7.2 14.5C7.35 15.4 8.1 16 9 16H18C18.85 16 19.6 15.4 19.75 14.5L21 7.5H6.5"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M13.5 6L10.5 11.5H14.5L11.5 17"
            stroke="#FEF08A"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <circle cx="9.5" cy="19.5" r="1.5" fill="currentColor" />
          <circle cx="17.5" cy="19.5" r="1.5" fill="currentColor" />
        </svg>
      </div>

      {/* ── Wordmark ── */}
      {showText && (
        <div className="flex flex-col leading-none">
          <div className={`font-black tracking-tight ${sizeConfig.text}`}>
            <span className="text-primary font-black">Razor</span>
            <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-sky-500 bg-clip-text text-transparent font-black">
              Hub
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
