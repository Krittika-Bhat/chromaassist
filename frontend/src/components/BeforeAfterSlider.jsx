import React, { useState, useRef, useCallback } from 'react';
import { ChevronsLeftRight } from 'lucide-react';

export default function BeforeAfterSlider({ originalSrc, modifiedSrc, modifiedLabel = 'Processed' }) {
  const [sliderPosition, setSliderPosition] = useState(50);
  const containerRef = useRef(null);
  const isDragging = useRef(false);

  const handleMove = useCallback((clientX) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    let position = (x / rect.width) * 100;
    if (position < 0) position = 0;
    if (position > 100) position = 100;
    setSliderPosition(position);
  }, []);

  const handleTouchMove = (e) => {
    if (e.touches && e.touches[0]) {
      handleMove(e.touches[0].clientX);
    }
  };

  const handleMouseDown = () => {
    isDragging.current = true;
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  const handleMouseMove = (e) => {
    if (isDragging.current) {
      handleMove(e.clientX);
    }
  };

  const handleMouseUp = () => {
    isDragging.current = false;
    window.removeEventListener('mousemove', handleMouseMove);
    window.removeEventListener('mouseup', handleMouseUp);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      setSliderPosition(prev => Math.max(0, prev - 5));
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      setSliderPosition(prev => Math.min(100, prev + 5));
    }
  };

  if (!originalSrc || !modifiedSrc) return null;

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center text-xs font-semibold text-slate-500 dark:text-slate-400 px-1">
        <span>← Original View</span>
        <span>{sliderPosition.toFixed(0)}% Split</span>
        <span>{modifiedLabel} View →</span>
      </div>

      <div
        ref={containerRef}
        className="relative w-full overflow-hidden select-none rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-950 aspect-video max-h-[520px] flex items-center justify-center cursor-ew-resize focus:outline-none focus:ring-2 focus:ring-brand-500"
        tabIndex={0}
        role="slider"
        aria-label="Before and after comparison slider"
        aria-valuenow={sliderPosition}
        aria-valuemin={0}
        aria-valuemax={100}
        onKeyDown={handleKeyDown}
        onTouchMove={handleTouchMove}
      >
        {/* Background Layer: Modified Image */}
        <img
          src={modifiedSrc}
          alt={modifiedLabel}
          className="absolute inset-0 w-full h-full object-contain pointer-events-none"
        />

        {/* Foreground Layer: Original Image (Clipped) */}
        <div
          className="absolute inset-0 overflow-hidden pointer-events-none"
          style={{ width: `${sliderPosition}%` }}
        >
          <img
            src={originalSrc}
            alt="Original"
            className="absolute inset-0 w-full h-full object-contain pointer-events-none"
            style={{
              width: containerRef.current ? `${containerRef.current.clientWidth}px` : '100%',
              maxWidth: 'none',
            }}
          />
        </div>

        {/* Divider Handle */}
        <div
          className="absolute top-0 bottom-0 z-20 w-0.5 bg-white shadow-lg pointer-events-auto"
          style={{ left: `${sliderPosition}%` }}
          onMouseDown={handleMouseDown}
          onTouchStart={() => (isDragging.current = true)}
          onTouchEnd={() => (isDragging.current = false)}
        >
          <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-white dark:bg-slate-900 border-2 border-brand-500 shadow-md flex items-center justify-center text-brand-600 dark:text-brand-400">
            <ChevronsLeftRight className="w-4 h-4" aria-hidden="true" />
          </div>
        </div>

        {/* Badges */}
        <span className="absolute top-3 left-3 z-10 text-[11px] font-bold tracking-wider uppercase px-2 py-1 rounded bg-black/70 text-white backdrop-blur-sm pointer-events-none">
          Original
        </span>
        <span className="absolute top-3 right-3 z-10 text-[11px] font-bold tracking-wider uppercase px-2 py-1 rounded bg-brand-900/80 text-brand-100 backdrop-blur-sm pointer-events-none">
          {modifiedLabel}
        </span>
      </div>
    </div>
  );
}
