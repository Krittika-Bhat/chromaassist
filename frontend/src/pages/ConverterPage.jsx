import React, { useState } from 'react';
import { Download, SlidersHorizontal, Image as ImageIcon, Sparkles, AlertCircle } from 'lucide-react';
import ImageDropzone from '../components/ImageDropzone';
import ControlPanel from '../components/ControlPanel';
import BeforeAfterSlider from '../components/BeforeAfterSlider';
import ComparisonGrid from '../components/ComparisonGrid';
import MetricsDisplay from '../components/MetricsDisplay';
import Toast from '../components/Toast';
import { processImage, compareImages } from '../utils/api';

export default function ConverterPage() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [params, setParams] = useState({
    deficiency: 'deuteranopia',
    severity: 1.0,
    mode: 'simulate',
    method: 'global',
    colormap: 'viridis',
  });

  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [processedResult, setProcessedResult] = useState(null);
  const [compareResult, setCompareResult] = useState(null);
  const [viewMode, setViewMode] = useState('single'); // 'single' | 'compare'

  // Trigger single image processing
  const handleProcess = async () => {
    if (!file) {
      setError('Please upload an image first.');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const data = await processImage({
        file,
        mode: params.mode,
        deficiency: params.deficiency,
        severity: params.severity,
        method: params.method,
        colormap: params.colormap,
      });
      setProcessedResult(data);
      setViewMode('single');
    } catch (err) {
      setError(err.message || 'Failed to process image. Make sure the backend server is running at http://localhost:8000.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Trigger 4-way comparison
  const handleCompare = async () => {
    if (!file) {
      setError('Please upload an image first.');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const data = await compareImages({
        file,
        deficiency: params.deficiency,
        severity: params.severity,
        method: params.method,
      });
      setCompareResult(data);
      setViewMode('compare');
    } catch (err) {
      setError(err.message || 'Failed to generate comparison. Make sure the backend server is running at http://localhost:8000.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Download the primary output image
  const handleDownload = () => {
    let b64 = null;
    let filename = `chroma-result-${params.deficiency}-${params.mode}.png`;

    if (viewMode === 'single' && processedResult?.processed_image_b64) {
      b64 = processedResult.processed_image_b64;
    } else if (viewMode === 'compare' && compareResult?.corrected_b64) {
      b64 = compareResult.corrected_b64;
      filename = `chroma-corrected-${params.deficiency}.png`;
    }

    if (!b64) return;

    const link = document.createElement('a');
    link.href = `data:image/png;base64,${b64}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const processedDataUrl = processedResult?.processed_image_b64
    ? `data:image/png;base64,${processedResult.processed_image_b64}`
    : null;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Header */}
      <div className="space-y-1">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
          Color Vision Deficiency Converter & Daltonizer
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-400 max-w-3xl">
          Simulate how images are perceived by individuals with Protanopia, Deuteranopia, or Tritanopia,
          and daltonize them to recover lost visual discrimination using physiological color-space transformations.
        </p>
      </div>

      {/* Main Grid: Upload & Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Image Upload & Preview */}
        <div className="lg:col-span-5 space-y-4">
          <ImageDropzone
            file={file}
            setFile={setFile}
            previewUrl={previewUrl}
            setPreviewUrl={setPreviewUrl}
            onError={setError}
          />
        </div>

        {/* Right Column: Processing Controls */}
        <div className="lg:col-span-7">
          <ControlPanel
            params={params}
            setParams={setParams}
            onProcess={handleProcess}
            onCompare={handleCompare}
            isProcessing={isProcessing}
            hasFile={!!file}
          />
        </div>
      </div>

      {/* Results Section */}
      {(processedResult || compareResult) && (
        <section aria-labelledby="results-heading" className="space-y-6 pt-4 border-t border-slate-200 dark:border-slate-800">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 id="results-heading" className="text-xl font-bold text-slate-900 dark:text-white flex items-center space-x-2">
                <span>Output & Comparative Results</span>
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Processed for {params.deficiency} at {params.severity * 100}% severity
              </p>
            </div>

            <div className="flex items-center space-x-2">
              {/* Switch View Buttons (if both available) */}
              {processedResult && compareResult && (
                <div className="inline-flex rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-0.5">
                  <button
                    type="button"
                    onClick={() => setViewMode('single')}
                    className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                      viewMode === 'single'
                        ? 'bg-brand-600 text-white shadow-sm'
                        : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'
                    }`}
                  >
                    Interactive Slider
                  </button>
                  <button
                    type="button"
                    onClick={() => setViewMode('compare')}
                    className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                      viewMode === 'compare'
                        ? 'bg-brand-600 text-white shadow-sm'
                        : 'text-slate-600 dark:text-slate-300 hover:text-slate-900'
                    }`}
                  >
                    4-Way Comparison
                  </button>
                </div>
              )}

              {/* Main Download Button */}
              <button
                type="button"
                onClick={handleDownload}
                className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-slate-900 dark:bg-slate-100 dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-white shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                <Download className="w-4 h-4" aria-hidden="true" />
                <span>Download Result PNG</span>
              </button>
            </div>
          </div>

          {/* View: Single Result with Interactive Slider */}
          {viewMode === 'single' && processedDataUrl && (
            <div className="space-y-4">
              <BeforeAfterSlider
                originalSrc={previewUrl}
                modifiedSrc={processedDataUrl}
                modifiedLabel={
                  params.mode === 'simulate'
                    ? 'Simulated'
                    : params.mode === 'correct'
                    ? 'Corrected'
                    : 'Pseudo-color'
                }
              />
            </div>
          )}

          {/* View: 4-Way Comparison Grid */}
          {viewMode === 'compare' && compareResult && (
            <ComparisonGrid compareData={compareResult} />
          )}

          {/* Metrics Panel */}
          <MetricsDisplay
            metrics={viewMode === 'single' ? processedResult?.metrics : compareResult?.metrics}
          />
        </section>
      )}

      {/* Floating Error Toast */}
      <Toast message={error} onClose={() => setError(null)} />
    </div>
  );
}
