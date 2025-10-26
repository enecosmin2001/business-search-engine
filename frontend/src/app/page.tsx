'use client';

import { useState } from 'react';
import SearchBar from '@/components/SearchBar';
import ResultsDisplay from '@/components/ResultsDisplay';
import ProgressTracker from '@/components/ProgressTracker';
import { createSearchTask, pollTaskStatus } from '@/app/api/api';
import type { TaskStatusResponse } from '@/types';

export default function Home() {
  const [isSearching, setIsSearching] = useState(false);
  const [currentStatus, setCurrentStatus] = useState<TaskStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (query: string) => {
    setIsSearching(true);
    setError(null);
    setCurrentStatus(null);

    try {
      // Create search task
      const taskResponse = await createSearchTask({
        query,
        include_website: true,
        include_linkedin: false,
      });

      console.log('Task created:', taskResponse.task_id);

      // Poll for results
      await pollTaskStatus(
        taskResponse.task_id,
        (status) => {
          console.log('Status update:', status);
          setCurrentStatus(status);
        },
        40, // max attempts
        3000 // 3 second interval
      );

    } catch (err) {
      console.error('Search failed:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                🔍 Business Search Engine
              </h1>
              <p className="mt-1 text-sm text-gray-600">
                AI-powered company information extraction
              </p>
            </div>
            <div className="text-right">
              <div className="text-xs text-gray-500">Powered by</div>
              <div className="text-sm font-semibold text-gray-700">
                FastAPI + Celery + LLM
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Search Section */}
        <div className="mb-12">
          <SearchBar
            onSearch={handleSearch}
            isLoading={isSearching}
          />
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <p className="mt-1 text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Progress Tracker */}
        {isSearching && currentStatus && (
          <div className="mb-8">
            <ProgressTracker status={currentStatus} />
          </div>
        )}

        {/* Results Display */}
        {currentStatus && currentStatus.status === 'completed' && currentStatus.result && (
          <ResultsDisplay
            companyInfo={currentStatus.result}
            taskInfo={{
              taskId: currentStatus.task_id,
              duration: currentStatus.duration_seconds,
              completedAt: currentStatus.completed_at,
            }}
          />
        )}

        {/* Empty State */}
        {!isSearching && !currentStatus && !error && (
          <div className="text-center py-20">
            <div className="inline-block p-6 bg-white rounded-full shadow-lg mb-6">
              <svg
                className="w-16 h-16 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-gray-700 mb-2">
              Search for any company
            </h2>
            <p className="text-gray-500 max-w-md mx-auto">
              Enter a company name above to extract detailed business information
              using AI-powered web scraping
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-2">
              {['Google Inc.', 'Tesla Motors', 'OpenAI', 'Microsoft'].map((example) => (
                <button
                  key={example}
                  onClick={() => handleSearch(example)}
                  className="px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:border-blue-500 hover:text-blue-600 transition-colors"
                >
                  Try: {example}
                </button>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-20 py-8 border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            Business Search Engine v0.1.0 • Built with Next.js 15 + FastAPI
          </p>
        </div>
      </footer>
    </div>
  );
}
