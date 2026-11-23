import React from 'react';
import { Eye, ShieldCheck, CheckCircle2, RefreshCw } from 'lucide-react';

export default function ComparisonGrid({ compareData }) {
  if (!compareData) return null;

  const panels = [
    {
      id: 'original',
      title: '1. Original Image',
      subtitle: 'Standard sRGB (Normal Trichromat Perception)',
      src: `data:image/png;base64,${compareData.original_b64}`,
      badgeColor: 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200 border-slate-300 dark:border-slate-700',
      icon: Eye,
    },
    {
      id: 'simulated',
      title: '2. CVD Simulated Original',
      subtitle: 'Lost contrast/hues as perceived without correction',
      src: `data:image/png;base64,${compareData.simulated_b64}`,
      badgeColor: 'bg-amber-50 text-amber-900 dark:bg-amber-950/60 dark:text-amber-200 border-amber-300 dark:border-amber-800',
      icon: RefreshCw,
    },
    {
      id: 'corrected',
      title: '3. Daltonized Corrected',
      subtitle: 'Errors shifted into blue channel & luminance',
      src: `data:image/png;base64,${compareData.corrected_b64}`,
      badgeColor: 'bg-blue-50 text-blue-900 dark:bg-blue-950/60 dark:text-blue-200 border-blue-300 dark:border-blue-800',
      icon: ShieldCheck,
    },
    {
      id: 'corrected_simulated',
      title: '4. Corrected then Simulated',
      subtitle: 'Predicted perception by CVD observer of the corrected image',
      src: `data:image/png;base64,${compareData.corrected_simulated_b64}`,
      badgeColor: 'bg-emerald-50 text-emerald-900 dark:bg-emerald-950/60 dark:text-emerald-200 border-emerald-300 dark:border-emerald-800',
      icon: CheckCircle2,
    },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-bold text-slate-900 dark:text-white">
          4-Way Comparative Analysis
        </h3>
        <span className="text-xs text-slate-500 dark:text-slate-400">
          Compare #2 vs #4 to verify visual information recovery
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {panels.map((p) => {
          const Icon = p.icon;
          return (
            <div
              key={p.id}
              className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm flex flex-col"
            >
              <div className="p-3.5 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between bg-slate-50/50 dark:bg-slate-900/40">
                <div className="flex items-center space-x-2 truncate">
                  <Icon className="w-4 h-4 text-brand-600 dark:text-brand-400 shrink-0" aria-hidden="true" />
                  <div className="truncate">
                    <p className="text-sm font-bold text-slate-900 dark:text-white truncate">
                      {p.title}
                    </p>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                      {p.subtitle}
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-slate-950 flex items-center justify-center min-h-[220px] max-h-[340px]">
                <img
                  src={p.src}
                  alt={p.title}
                  className="max-h-[300px] w-auto max-w-full object-contain rounded"
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
