'use client';

import { useState, FormEvent } from 'react';
import { Search, Loader2 } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

export default function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto">
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          {isLoading ? (
            <Loader2 className="h-5 w-5 text-gray-400 animate-spin" />
          ) : (
            <Search className="h-5 w-5 text-gray-400" />
          )}
        </div>

        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter company name (e.g., Google Inc., Tesla Motors...)"
          disabled={isLoading}
          className="w-full pl-12 pr-32 py-4 text-lg border-2 border-gray-300 rounded-xl
                     focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200
                     disabled:bg-gray-100 disabled:cursor-not-allowed
                     transition-all duration-200 shadow-sm"
        />

        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2.5
                     bg-blue-600 text-white font-medium rounded-lg
                     hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                     disabled:bg-gray-300 disabled:cursor-not-allowed
                     transition-all duration-200 shadow-sm"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Searching...
            </span>
          ) : (
            'Search'
          )}
        </button>
      </div>

      <div className="mt-3 flex items-center justify-center gap-4 text-sm text-gray-600">
        <span className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 bg-green-500 rounded-full"></span>
          AI-Powered
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 bg-blue-500 rounded-full"></span>
          Web Scraping
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 bg-purple-500 rounded-full"></span>
          Real-time Results
        </span>
      </div>
    </form>
  );
}
