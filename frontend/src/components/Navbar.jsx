import React from 'react';
import { NavLink } from 'react-router-dom';
import { Eye, Sun, Moon } from 'lucide-react';

export default function Navbar({ darkMode, setDarkMode }) {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <NavLink
          to="/"
          className="flex items-center space-x-2.5 text-slate-900 dark:text-white font-bold text-lg tracking-tight focus:outline-none focus:ring-2 focus:ring-brand-500 rounded-md p-1"
        >
          <div className="w-8 h-8 rounded-lg bg-brand-600 text-white flex items-center justify-center shadow-sm">
            <Eye className="w-5 h-5" aria-hidden="true" />
          </div>
          <span>Chroma<span className="text-brand-600 dark:text-brand-400">Assist</span></span>
        </NavLink>

        {/* Navigation & Controls */}
        <div className="flex items-center space-x-2 sm:space-x-6">
          <nav className="flex space-x-1 sm:space-x-2" aria-label="Main Navigation">
            <NavLink
              to="/"
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 ${
                  isActive
                    ? 'bg-slate-100 text-brand-600 dark:bg-slate-800 dark:text-brand-400 font-semibold'
                    : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800/60'
                }`
              }
            >
              Converter
            </NavLink>
            <NavLink
              to="/about"
              className={({ isActive }) =>
                `px-3 py-1.5 rounded-md text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 ${
                  isActive
                    ? 'bg-slate-100 text-brand-600 dark:bg-slate-800 dark:text-brand-400 font-semibold'
                    : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800/60'
                }`
              }
            >
              About & Science
            </NavLink>
          </nav>

          {/* Dark Mode Toggle */}
          <button
            type="button"
            onClick={() => setDarkMode(!darkMode)}
            aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            className="p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors"
          >
            {darkMode ? (
              <Sun className="w-5 h-5 text-amber-400" aria-hidden="true" />
            ) : (
              <Moon className="w-5 h-5 text-slate-700" aria-hidden="true" />
            )}
          </button>
        </div>
      </div>
    </header>
  );
}
