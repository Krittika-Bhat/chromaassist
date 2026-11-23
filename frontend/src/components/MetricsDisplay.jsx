import React from 'react';
import { BarChart3, Info, CheckCircle, Percent, Pipette } from 'lucide-react';

export default function MetricsDisplay({ metrics }) {
  if (!metrics) return null;

  const origDeltaE = metrics.original_vs_simulated_delta_e;
  const corrDeltaE = metrics.corrected_vs_its_simulation_delta_e;
  const regionStats = metrics.region_stats;

  // Has correction improved the score?
  const isImproved = corrDeltaE < origDeltaE;
  const reductionPct = origDeltaE > 0 ? (((origDeltaE - corrDeltaE) / origDeltaE) * 100).toFixed(1) : 0;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm space-y-5">
      <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-700 pb-3">
        <div className="flex items-center space-x-2">
          <BarChart3 className="w-5 h-5 text-brand-600 dark:text-brand-400" aria-hidden="true" />
          <h3 className="text-base font-bold text-slate-900 dark:text-white">
            Perceptual Quality Metrics (CIELAB ΔE)
          </h3>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-700 font-mono text-slate-700 dark:text-slate-300">
          CIE 1976 ΔE₇₆
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Whole-image Information Lost: Original vs Simulated */}
        <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/40 space-y-1">
          <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            Information Lost: Original vs. Simulated
          </p>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-extrabold font-mono text-slate-900 dark:text-white">
              {origDeltaE != null ? Number(origDeltaE).toFixed(2) : '—'}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">ΔE</span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Whole-image color distortion caused by the deficiency without correction. (Lower is better)
          </p>
        </div>

        {/* Whole-image Information Lost: Corrected vs Simulated */}
        <div className="p-4 rounded-lg border border-brand-200 dark:border-brand-900/60 bg-brand-50/40 dark:bg-brand-950/20 space-y-1">
          <p className="text-xs font-semibold text-brand-700 dark:text-brand-300 uppercase tracking-wider flex items-center justify-between">
            <span>Information Lost: Corrected vs. Simulated</span>
            {isImproved && (
              <span className="inline-flex items-center text-[10px] text-emerald-700 dark:text-emerald-300 font-bold bg-emerald-100 dark:bg-emerald-950/80 px-1.5 py-0.5 rounded">
                ↓ {reductionPct}% reduction
              </span>
            )}
          </p>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-extrabold font-mono text-brand-600 dark:text-brand-400">
              {corrDeltaE != null ? Number(corrDeltaE).toFixed(2) : '—'}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">ΔE</span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Residual whole-image color distortion after daltonization. (Lower is better)
          </p>
        </div>
      </div>

      {/* Pair Discriminability Card (Primary Effectiveness Metric) */}
      {metrics.pair_discriminability && metrics.pair_discriminability.valid && (
        <div className="p-4 rounded-lg border border-emerald-300 dark:border-emerald-800 bg-emerald-50/70 dark:bg-emerald-950/40 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-900 dark:text-emerald-200 flex items-center space-x-1.5">
              <CheckCircle className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" aria-hidden="true" />
              <span>
                Confusable Pair Discriminability ({metrics.pair_discriminability.group1_name} vs. {metrics.pair_discriminability.group2_name})
              </span>
            </h4>
            {metrics.pair_discriminability.improvement_pct > 0 && (
              <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-200 dark:bg-emerald-900 text-emerald-900 dark:text-emerald-100 w-fit">
                +{metrics.pair_discriminability.improvement_pct}% Contrast Gain
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="space-y-0.5">
              <p className="font-semibold text-slate-700 dark:text-slate-300">Pair ΔE (Simulated Original)</p>
              <p className="text-xl font-extrabold font-mono text-slate-900 dark:text-white">
                {metrics.pair_discriminability.delta_e_simulated_original?.toFixed(2)} ΔE
              </p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                Baseline separation between confusable colors before correction
              </p>
            </div>

            <div className="space-y-0.5">
              <p className="font-semibold text-emerald-800 dark:text-emerald-300">Pair ΔE (Simulated Corrected)</p>
              <p className="text-xl font-extrabold font-mono text-emerald-700 dark:text-emerald-300">
                {metrics.pair_discriminability.delta_e_simulated_corrected?.toFixed(2)} ΔE
              </p>
              <p className="text-[11px] text-emerald-800 dark:text-emerald-300 font-semibold">
                HIGHER = the two colors are easier to tell apart
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Plain Language Interpretation Alert */}
      <div className="flex items-start space-x-2.5 p-3 rounded-lg bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900 text-xs text-blue-900 dark:text-blue-200">
        <Info className="w-4 h-4 text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" aria-hidden="true" />
        <p className="leading-relaxed">
          {metrics.delta_e_note || (
            <>
              <strong>Interpretation:</strong> Lower ΔE values indicate that less color information is lost.
              A successful correction produces a lower &quot;Corrected vs. Simulation&quot; ΔE than the uncorrected baseline.
            </>
          )}
        </p>
      </div>

      {/* Targeted Mode Region Stats (if available) */}
      {regionStats && (
        <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/40 space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center space-x-1.5">
            <Pipette className="w-4 h-4 text-brand-600 dark:text-brand-400" aria-hidden="true" />
            <span>Targeted Region Mask Statistics</span>
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            {/* Area % */}
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded bg-brand-100 dark:bg-brand-900/50 text-brand-600 dark:text-brand-400">
                <Percent className="w-4 h-4" />
              </div>
              <div>
                <p className="font-semibold text-slate-500 dark:text-slate-400">Segmented Confusion Area</p>
                <p className="text-base font-bold font-mono text-slate-900 dark:text-white">
                  {regionStats.area_pct}% of total image
                </p>
              </div>
            </div>

            {/* Mean Color */}
            {regionStats.mean_color && (
              <div className="flex items-center space-x-3">
                <div
                  className="w-9 h-9 rounded-md border border-slate-300 dark:border-slate-600 shadow-sm shrink-0"
                  style={{
                    backgroundColor: `rgb(${Math.round(regionStats.mean_color[0])}, ${Math.round(regionStats.mean_color[1])}, ${Math.round(regionStats.mean_color[2])})`
                  }}
                  title={`RGB(${Math.round(regionStats.mean_color[0])}, ${Math.round(regionStats.mean_color[1])}, ${Math.round(regionStats.mean_color[2])})`}
                  aria-label="Targeted mask mean color swatch"
                />
                <div>
                  <p className="font-semibold text-slate-500 dark:text-slate-400">Mask Mean Color (RGB)</p>
                  <p className="font-mono text-slate-900 dark:text-white">
                    [{Math.round(regionStats.mean_color[0])}, {Math.round(regionStats.mean_color[1])}, {Math.round(regionStats.mean_color[2])}]
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
