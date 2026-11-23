import React from 'react';
import { AlertCircle, X } from 'lucide-react';

export default function Toast({ message, onClose }) {
  if (!message) return null;

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="fixed bottom-5 right-5 z-50 flex items-start max-w-md p-4 space-x-3 text-slate-800 bg-red-50 border border-red-200 rounded-lg shadow-lg dark:bg-red-950 dark:text-red-200 dark:border-red-900"
    >
      <AlertCircle className="w-5 h-5 mt-0.5 text-red-600 dark:text-red-400 shrink-0" aria-hidden="true" />
      <div className="flex-1 text-sm font-medium leading-relaxed">
        {message}
      </div>
      <button
        type="button"
        onClick={onClose}
        aria-label="Dismiss alert"
        className="text-red-500 hover:text-red-700 dark:text-red-400 dark:hover:text-red-200 focus:outline-none focus:ring-2 focus:ring-red-400 rounded p-0.5"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
