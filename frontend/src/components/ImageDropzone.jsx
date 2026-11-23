import React, { useRef, useState } from 'react';
import { UploadCloud, Image as ImageIcon, X, AlertTriangle } from 'lucide-react';

const MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB
const ALLOWED_TYPES = ['image/png', 'image/jpeg'];
const ALLOWED_EXTS = ['.png', '.jpg', '.jpeg'];

export default function ImageDropzone({ file, setFile, previewUrl, setPreviewUrl, onError }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef(null);

  const validateAndSetFile = (selectedFile) => {
    if (!selectedFile) return;

    // Check extension and mime type
    const lowerName = selectedFile.name.toLowerCase();
    const hasValidExt = ALLOWED_EXTS.some(ext => lowerName.endsWith(ext));
    const hasValidType = ALLOWED_TYPES.includes(selectedFile.type);

    if (!hasValidExt && !hasValidType) {
      onError('Unsupported file type. Please upload a PNG or JPEG image only.');
      return;
    }

    if (selectedFile.size > MAX_SIZE_BYTES) {
      const sizeMb = (selectedFile.size / (1024 * 1024)).toFixed(2);
      onError(`File size (${sizeMb} MB) exceeds the 10 MB limit. Please select a smaller image.`);
      return;
    }

    // Clear any previous error and update file + preview
    onError(null);
    setFile(selectedFile);

    const objectUrl = URL.createObjectURL(selectedFile);
    setPreviewUrl(objectUrl);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleClear = () => {
    setFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    onError(null);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  return (
    <div className="w-full">
      <input
        ref={inputRef}
        type="file"
        id="image-upload-input"
        accept="image/png, image/jpeg"
        onChange={handleFileChange}
        className="sr-only"
        aria-label="Upload PNG or JPEG image up to 10 MB"
      />

      {!file ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              inputRef.current?.click();
            }
          }}
          className={`relative border-2 border-dashed rounded-xl p-8 sm:p-12 text-center cursor-pointer transition-all focus:outline-none focus:ring-2 focus:ring-brand-500 ${
            isDragOver
              ? 'border-brand-500 bg-brand-50/60 dark:bg-brand-950/30'
              : 'border-slate-300 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-600 bg-white dark:bg-slate-800/40'
          }`}
        >
          <div className="flex flex-col items-center justify-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-brand-100 dark:bg-brand-900/50 flex items-center justify-center text-brand-600 dark:text-brand-400">
              <UploadCloud className="w-6 h-6" aria-hidden="true" />
            </div>
            <div>
              <p className="text-base font-semibold text-slate-900 dark:text-white">
                Drag and drop your image here, or <span className="text-brand-600 dark:text-brand-400 underline">browse</span>
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Supports PNG and JPG/JPEG up to 10 MB (images &gt; 1600px auto-downscaled)
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="relative border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-700">
            <div className="flex items-center space-x-2.5 truncate">
              <ImageIcon className="w-5 h-5 text-brand-600 dark:text-brand-400 shrink-0" aria-hidden="true" />
              <div className="truncate">
                <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">
                  {file.name}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={handleClear}
              aria-label="Remove uploaded image"
              className="p-1.5 rounded-lg text-slate-500 hover:text-red-600 dark:text-slate-400 dark:hover:text-red-400 hover:bg-slate-100 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-red-400 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="mt-3 flex justify-center bg-slate-100 dark:bg-slate-900 rounded-lg p-2 max-h-64 overflow-hidden">
            <img
              src={previewUrl}
              alt="Uploaded original preview"
              className="max-h-56 max-w-full object-contain rounded"
            />
          </div>
        </div>
      )}
    </div>
  );
}
