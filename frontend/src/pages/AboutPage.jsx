import React from 'react';
import { BookOpen, Eye, ShieldAlert, Cpu, Sparkles, AlertTriangle, Layers, Palette } from 'lucide-react';

export default function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Hero */}
      <div className="space-y-3">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-brand-50 dark:bg-brand-950/60 border border-brand-200 dark:border-brand-900 text-xs font-semibold text-brand-700 dark:text-brand-300">
          <BookOpen className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Scientific Background & Methodology</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          How ChromaAssist Works
        </h1>
        <p className="text-base text-slate-600 dark:text-slate-300 leading-relaxed">
          ChromaAssist applies digital image processing and color science principles to simulate
          and compensate for human color vision deficiencies (CVD).
        </p>
      </div>

      {/* 1. What is Color Vision Deficiency? */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center space-x-2">
          <Eye className="w-5 h-5 text-brand-600 dark:text-brand-400" aria-hidden="true" />
          <span>1. Understanding Color Vision Deficiency (CVD)</span>
        </h2>
        <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
          Normal human vision is <strong>trichromatic</strong>, mediated by three classes of cone photoreceptors
          in the retina that are sensitive to different wavelengths of light:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <div className="p-4 rounded-xl border border-red-200 dark:border-red-900/60 bg-red-50/40 dark:bg-red-950/20 space-y-1.5">
            <span className="text-xs font-bold text-red-700 dark:text-red-400 uppercase tracking-wider">
              L-Cones (Long / Red)
            </span>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">Protanopia</h3>
            <p className="text-xs text-slate-600 dark:text-slate-300">
              Absence or mutation of L-cones. Red hues appear darkened and are easily confused with black, brown, and green.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/40 dark:bg-emerald-950/20 space-y-1.5">
            <span className="text-xs font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider">
              M-Cones (Medium / Green)
            </span>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">Deuteranopia</h3>
            <p className="text-xs text-slate-600 dark:text-slate-300">
              Absence or mutation of M-cones (most common, ~6% of males). Greens and reds collapse toward similar yellowish-brown hues.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-blue-200 dark:border-blue-900/60 bg-blue-50/40 dark:bg-blue-950/20 space-y-1.5">
            <span className="text-xs font-bold text-blue-700 dark:text-blue-400 uppercase tracking-wider">
              S-Cones (Short / Blue)
            </span>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">Tritanopia</h3>
            <p className="text-xs text-slate-600 dark:text-slate-300">
              Absence or mutation of S-cones (rare, &lt;0.01% of population). Blues are confused with greens, and yellows with violet or light gray.
            </p>
          </div>
        </div>
      </section>

      {/* 2. Simulation Pipeline */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center space-x-2">
          <Cpu className="w-5 h-5 text-brand-600 dark:text-brand-400" aria-hidden="true" />
          <span>2. The Simulation Pipeline (Machado et al. 2009)</span>
        </h2>
        <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 space-y-3 text-sm text-slate-600 dark:text-slate-300">
          <p>
            ChromaAssist simulates color vision deficiency without third-party black-box libraries by implementing
            the physiologically-based model published by <em>Machado, Oliveira &amp; Fernandes (IEEE TVCG 2009)</em>:
          </p>
          <ol className="list-decimal list-inside space-y-2 pl-2">
            <li>
              <strong>Gamma De-quantization (sRGB &rarr; Linear RGB):</strong> Because digital sRGB values incorporate
              non-linear monitor gamma (~2.2/2.4 curve), pixels must first be converted into linear light space where photon mixing is mathematically linear.
            </li>
            <li>
              <strong>Physiological 3&times;3 Matrix Projection:</strong> Pixels are multiplied by the Machado spectral projection matrix,
              which collapses the deficient cone dimension onto the remaining functional cone axes.
            </li>
            <li>
              <strong>Severity Interpolation:</strong> Partial deficiencies (anomalous trichromacy) are modeled via linear interpolation between the identity matrix <code className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-700 font-mono text-xs">I</code> (severity 0) and the full matrix <code className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-700 font-mono text-xs">M</code> (severity 1).
            </li>
            <li>
              <strong>Re-encoding (Linear RGB &rarr; sRGB):</strong> Results are clipped to [0, 1] and the standard IEC 61966-2-1 piecewise gamma function is reapplied.
            </li>
          </ol>
        </div>
      </section>

      {/* 3. Daltonization Algorithm */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center space-x-2">
          <Layers className="w-5 h-5 text-brand-600 dark:text-brand-400" aria-hidden="true" />
          <span>3. Daltonization &amp; Information Redistribution</span>
        </h2>
        <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 space-y-3 text-sm text-slate-600 dark:text-slate-300">
          <p>
            Daltonization redistributes visual information from channels the viewer <em>cannot</em> perceive into channels they <em>can</em> perceive:
          </p>
          <ul className="list-disc list-inside space-y-1.5 pl-2">
            <li>
              <strong>Error Signal Computation:</strong> An error map is computed as <code className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-700 font-mono text-xs">E = Original - Simulated</code>.
              This represents the exact chromatic contrast lost to the deficiency.
            </li>
            <li>
              <strong>Channel Shift Matrix:</strong> A transformation matrix <code className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-700 font-mono text-xs">M</code> shifts the lost red-green information into the blue channel and luminance.
            </li>
            <li>
              <strong>Targeted Segmentation:</strong> In targeted mode, the image is converted to HSV space to isolate specific confusion hues (reds, greens, oranges, browns). Morphological opening and closing clean up isolated noise, ensuring only confusing regions are altered while leaving natural background elements intact.
            </li>
            <li>
              <strong>Pseudo-Coloring:</strong> As an alternative for diagrams and data charts, intensity luminance is mapped directly onto CVD-uniform color scales such as <em>Viridis</em> or <em>Cividis</em>.
            </li>
          </ul>
        </div>
      </section>

      {/* 4. Limitations */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-amber-700 dark:text-amber-400 flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5" aria-hidden="true" />
          <span>4. Important Limitations &amp; Caveats</span>
        </h2>
        <div className="p-5 rounded-xl border border-amber-200 dark:border-amber-900/60 bg-amber-50/30 dark:bg-amber-950/20 space-y-3 text-sm text-slate-700 dark:text-slate-300">
          <div className="space-y-2">
            <p>
              <strong>Distinction over Naturalness:</strong> Daltonization is designed to maximize <em>contrast and discriminability</em> between otherwise indistinguishable elements (e.g., distinguishing green and red lines on a subway map or data chart). It does not recreate true physiological trichromatic vision.
            </p>
            <p>
              <strong>Visual Artifacts for Trichromats:</strong> To individuals with normal color vision, daltonized images will often look oversaturated, blue-tinted, or unnatural because color differences have been artificially exaggerated.
            </p>
            <p>
              <strong>Individual Variation:</strong> Real-world color blindness is a spectrum with genetic and physiological variations. A severity setting of 1.0 represents textbook complete dichromacy; real individuals may benefit from adjusting the severity slider.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
