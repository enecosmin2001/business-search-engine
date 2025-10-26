'use client';

import { Loader2, Database, Brain, CheckCircle2 } from 'lucide-react';
import type { TaskStatusResponse } from '@/types';
import { getStatusColor } from '@/utils/utils';
import { cn } from '@/utils/utils';

interface ProgressTrackerProps {
  status: TaskStatusResponse;
}

export default function ProgressTracker({ status }: ProgressTrackerProps) {
  const steps = [
    { id: 'pending', label: 'Queued', icon: Loader2, threshold: 0 },
    { id: 'scraping', label: 'Scraping', icon: Database, threshold: 20 },
    { id: 'processing', label: 'Processing', icon: Brain, threshold: 60 },
    { id: 'completed', label: 'Complete', icon: CheckCircle2, threshold: 100 },
  ];

  const getCurrentStepIndex = () => {
    const statusMap: Record<string, number> = {
      'pending': 0,
      'started': 1,
      'scraping': 1,
      'processing': 2,
      'completed': 3,
      'failed': -1,
    };
    return statusMap[status.status] ?? 0;
  };

  const currentStepIndex = getCurrentStepIndex();

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Processing Search</h3>
          <p className="text-sm text-gray-600 mt-1">
            {status.message || 'Please wait...'}
          </p>
        </div>
        <div className={cn(
          'px-3 py-1 rounded-full text-xs font-medium border',
          getStatusColor(status.status)
        )}>
          {status.status.toUpperCase()}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Progress</span>
          <span className="text-sm font-medium text-blue-600">{status.progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-500 ease-out"
            style={{ width: `${status.progress}%` }}
          >
            <div className="w-full h-full bg-white/30 animate-pulse"></div>
          </div>
        </div>
      </div>

      {/* Steps */}
      <div className="grid grid-cols-4 gap-4">
        {steps.map((step, index) => {
          const Icon = step.icon;
          const isActive = index === currentStepIndex;
          const isCompleted = index < currentStepIndex;
          const isPending = index > currentStepIndex;

          return (
            <div
              key={step.id}
              className={cn(
                'flex flex-col items-center text-center transition-all duration-300',
                isActive && 'scale-110'
              )}
            >
              <div
                className={cn(
                  'w-12 h-12 rounded-full flex items-center justify-center mb-2 transition-all',
                  isCompleted && 'bg-green-500 text-white',
                  isActive && 'bg-blue-500 text-white shadow-lg ring-4 ring-blue-100',
                  isPending && 'bg-gray-200 text-gray-400'
                )}
              >
                <Icon
                  className={cn(
                    'w-6 h-6',
                    isActive && 'animate-pulse'
                  )}
                />
              </div>
              <span
                className={cn(
                  'text-xs font-medium transition-colors',
                  isCompleted && 'text-green-600',
                  isActive && 'text-blue-600',
                  isPending && 'text-gray-400'
                )}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Task Info */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Task ID: {status.task_id.substring(0, 8)}...</span>
          {status.started_at && (
            <span>Started: {new Date(status.started_at).toLocaleTimeString()}</span>
          )}
        </div>
      </div>
    </div>
  );
}
