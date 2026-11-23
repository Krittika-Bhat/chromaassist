import React from 'react';
import { Sliders, Play, Layers, Loader2, Sparkles, Eye, ShieldCheck, Palette } from 'lucide-react';

const DEFICIENCIES = [
  { id: 'deuteranopia', label: 'Deuteranopia (Green-blind)' },
  { id: 'protanopia', label: 'Protanopia (Red-blind)' },
  { id: 'tritanopia', label: 'Tritanopia (Blue-blind)' },
];

const MODES = [
  { id: 'simulate', label: 'Simulate', desc: 'Simulate CVD view (Machado 2009)', icon: Eye },
  { id: 'correct', label: 'Correct', desc: 'Daltonize channel shift', icon: ShieldCheck },
  { id: 'pseudocolor', label: 'Pseudo-color', desc: 'Map intensity to CVD-safe colormap', icon: Palette },
];

const METHODS = [
  { id: 'global', label: 'Global', desc: 'Correct across all pixels' },
  { id: 'targeted', label: 'Targeted', desc: 'HSV-segmented confusing hues only' },
];

const COLORMAPS = [
  { id: 'viridis', label: 'Viridis (Default)', desc: 'Perceptually uniform blue-green-yellow' },
  { id: 'cividis', label: 'Cividis', desc: 'Optimized specifically for red-green CVD' },
];

export default function ControlPanel({
  params,
  setParams,
  onProcess,
  onCompare,
  isProcessing,
  hasFile,
}) {
  const handleChange = (key, value) => {
    setParams(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm space-y-6">
      <div className="flex items-center space-x-2 border-b border-slate-100 dark:border-slate-700 pb-3">
        <Sliders className="w-5 h-5 text-brand-600 dark:text-brand-400" aria-hidden="true" />
        <h2 className="text-base font-bold text-slate-900 dark:text-white">
          Configuration & Controls
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Deficiency Type */}
        <div className="space-y-1.5">
          <label htmlFor="deficiency-select" className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300">
            Deficiency Type
          </label>
          <select
            id="deficiency-select"
            value={params.deficiency}
            onChange={(e) => handleChange('deficiency', e.target.value)}
            className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            {DEFICIENCIES.map(d => (
              <option key={d.id} value={d.id}>
                {d.label}
              </option>
            ))}
          </select>
        </div>

        {/* Severity Slider */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-center">
            <label htmlFor="severity-slider" className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300">
              Severity Level
            </label>
            <span className="text-sm font-bold font-mono text-brand-600 dark:text-brand-400">
              {Number(params.severity).toFixed(2)}
            </span>
          </div>
          <input
            id="severity-slider"
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={params.severity}
            onChange={(e) => handleChange('severity', parseFloat(e.target.value))}
            className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <div className="flex justify-between text-[11px] text-slate-400">
            <span>0.0 (Original / Normal)</span>
            <span>1.0 (Complete Dichromacy)</span>
          </div>
        </div>
      </div>

      {/* Mode Selection */}
      <div className="space-y-2">
        <span className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300">
          Processing Mode
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          {MODES.map(m => {
            const Icon = m.icon;
            const isSelected = params.mode === m.id;
            return (
              <button
                key={m.id}
                type="button"
                onClick={() => handleChange('mode', m.id)}
                className={`flex flex-col items-start p-3 rounded-lg border text-left transition-all focus:outline-none focus:ring-2 focus:ring-brand-500 ${
                  isSelected
                    ? 'border-blue-600 dark:border-blue-400 bg-blue-50/90 dark:bg-blue-950/80 ring-2 ring-blue-500 shadow-sm'
                    : 'border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/40 hover:bg-slate-100 dark:hover:bg-slate-800/80'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Icon className={`w-4 h-4 ${isSelected ? 'text-blue-600 dark:text-blue-400' : 'text-slate-500 dark:text-slate-400'}`} />
                  <span className={`text-sm ${isSelected ? 'font-extrabold text-blue-950 dark:text-white' : 'font-bold text-slate-800 dark:text-slate-200'}`}>
                    {m.label}
                  </span>
                </div>
                <span className={`text-xs mt-1 ${isSelected ? 'font-medium text-blue-900 dark:text-blue-100' : 'text-slate-500 dark:text-slate-400'}`}>
                  {m.desc}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Method Selection (Only for Correct mode) */}
      {params.mode === 'correct' && (
        <div className="p-4 bg-slate-50 dark:bg-slate-900/70 rounded-lg border border-slate-200 dark:border-slate-700 space-y-2">
          <span className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300">
            Daltonization Method
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {METHODS.map(met => {
              const isSelected = params.method === met.id;
              return (
                <button
                  key={met.id}
                  type="button"
                  onClick={() => handleChange('method', met.id)}
                  className={`p-3 rounded-lg border text-left transition-all focus:outline-none focus:ring-2 focus:ring-brand-500 ${
                    isSelected
                      ? 'border-brand-600 bg-white dark:bg-slate-800 text-brand-900 dark:text-brand-100 ring-1 ring-brand-500 shadow-sm'
                      : 'border-slate-300 dark:border-slate-700 bg-transparent text-slate-700 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-800'
                  }`}
                >
                  <p className="text-sm font-semibold">{met.label} Method</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{met.desc}</p>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Colormap Selection (Only for Pseudo-color mode) */}
      {params.mode === 'pseudocolor' && (
        <div className="p-4 bg-slate-50 dark:bg-slate-900/70 rounded-lg border border-slate-200 dark:border-slate-700 space-y-2">
          <span className="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300">
            Colormap Palette
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {COLORMAPS.map(cm => {
              const isSelected = params.colormap === cm.id;
              return (
                <button
                  key={cm.id}
                  type="button"
                  onClick={() => handleChange('colormap', cm.id)}
                  className={`p-3 rounded-lg border text-left transition-all focus:outline-none focus:ring-2 focus:ring-brand-500 ${
                    isSelected
                      ? 'border-brand-600 bg-white dark:bg-slate-800 text-brand-900 dark:text-brand-100 ring-1 ring-brand-500 shadow-sm'
                      : 'border-slate-300 dark:border-slate-700 bg-transparent text-slate-700 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-800'
                  }`}
                >
                  <p className="text-sm font-semibold">{cm.label}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{cm.desc}</p>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3 pt-2">
        <button
          type="button"
          onClick={onProcess}
          disabled={!hasFile || isProcessing}
          className="flex-1 inline-flex items-center justify-center space-x-2 px-5 py-3 rounded-lg font-semibold text-white bg-brand-600 hover:bg-brand-700 active:bg-brand-800 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 dark:focus:ring-offset-slate-900"
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" aria-hidden="true" />
              <span>Processing image...</span>
            </>
          ) : (
            <>
              <Play className="w-5 h-5" aria-hidden="true" />
              <span>Process Image</span>
            </>
          )}
        </button>

        <button
          type="button"
          onClick={onCompare}
          disabled={!hasFile || isProcessing}
          className="inline-flex items-center justify-center space-x-2 px-5 py-3 rounded-lg font-semibold text-slate-800 dark:text-slate-200 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 active:bg-slate-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400"
        >
          <Layers className="w-5 h-5 text-slate-600 dark:text-slate-300" aria-hidden="true" />
          <span>Compare All (4-Way)</span>
        </button>
      </div>
    </div>
  );
}
