import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import ConverterPage from './pages/ConverterPage';
import AboutPage from './pages/AboutPage';

export default function App() {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('chroma_dark_mode');
    if (saved !== null) {
      return saved === 'true';
    }
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    localStorage.setItem('chroma_dark_mode', darkMode);
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 transition-colors duration-150">
        <Navbar darkMode={darkMode} setDarkMode={setDarkMode} />

        <main className="flex-1">
          <Routes>
            <Route path="/" element={<ConverterPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>

        <footer className="border-t border-slate-200 dark:border-slate-800 py-6 bg-white dark:bg-slate-900/60 text-center text-xs text-slate-500 dark:text-slate-400">
          <p>
            ChromaAssist &mdash; Colorblind-Friendly Image Converter &amp; Daltonizer
          </p>
          <p className="mt-1">
            Engineered with React, Vite, Tailwind CSS &amp; FastAPI
          </p>
        </footer>
      </div>
    </Router>
  );
}
