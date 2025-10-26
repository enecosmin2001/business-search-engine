'use client';

import {
  Building2,
  Globe,
  Users,
  MapPin,
  Calendar,
  Briefcase,
  Download,
  ExternalLink,
  TrendingUp
} from 'lucide-react';
import type { CompanyInfo } from '@/types';
import {
  formatNumber,
  formatDuration,
  getConfidenceColor,
  exportAsJSON
} from '@/utils/utils';

interface ResultsDisplayProps {
  companyInfo: CompanyInfo;
  taskInfo: {
    taskId: string;
    duration: number | null;
    completedAt: string | null;
  };
}

export default function ResultsDisplay({ companyInfo, taskInfo }: ResultsDisplayProps) {
  const handleExport = () => {
    const data = {
      company: companyInfo,
      metadata: {
        taskId: taskInfo.taskId,
        duration: taskInfo.duration,
        completedAt: taskInfo.completedAt,
        exportedAt: new Date().toISOString(),
      },
    };
    exportAsJSON(data, `${companyInfo.marketing_name || 'company'}-data.json`);
  };

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <Building2 className="w-8 h-8 text-blue-600" />
              <h2 className="text-3xl font-bold text-gray-900">
                {companyInfo.marketing_name || companyInfo.legal_name || 'Unknown Company'}
              </h2>
            </div>
            {companyInfo.legal_name && companyInfo.marketing_name !== companyInfo.legal_name && (
              <p className="text-sm text-gray-600 mb-2">
                Legal Name: {companyInfo.legal_name}
              </p>
            )}
            {companyInfo.description && (
              <p className="text-gray-700 mt-4 leading-relaxed">
                {companyInfo.description}
              </p>
            )}
          </div>

          {/* Confidence Score */}
          {companyInfo.confidence_score !== null && (
            <div className="ml-4 text-center">
              <div className="text-xs text-gray-500 mb-1">Confidence</div>
              <div className={`text-3xl font-bold ${getConfidenceColor(companyInfo.confidence_score)}`}>
                {Math.round(companyInfo.confidence_score * 100)}%
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="mt-6 flex gap-3">
          {companyInfo.website && (
            <a
              href={companyInfo.website}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Globe className="w-4 h-4" />
              Visit Website
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
          {companyInfo.linkedin_url && (
            <a
              href={companyInfo.linkedin_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-[#0A66C2] text-white rounded-lg hover:bg-[#004182] transition-colors"
            >
              LinkedIn
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
          <button
            onClick={handleExport}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors ml-auto"
          >
            <Download className="w-4 h-4" />
            Export JSON
          </button>
        </div>
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Website */}
        {companyInfo.website && (
          <InfoCard
            icon={<Globe className="w-5 h-5" />}
            label="Website"
            value={
              <a
                href={companyInfo.website}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline flex items-center gap-1"
              >
                {new URL(companyInfo.website).hostname}
                <ExternalLink className="w-3 h-3" />
              </a>
            }
          />
        )}

        {/* Employees */}
        {(companyInfo.employee_count || companyInfo.employee_range) && (
          <InfoCard
            icon={<Users className="w-5 h-5" />}
            label="Employees"
            value={
              companyInfo.employee_count
                ? formatNumber(companyInfo.employee_count)
                : companyInfo.employee_range
            }
          />
        )}

        {/* Industry */}
        {companyInfo.industry && (
          <InfoCard
            icon={<Briefcase className="w-5 h-5" />}
            label="Industry"
            value={companyInfo.industry}
          />
        )}

        {/* Founded */}
        {companyInfo.founded_year && (
          <InfoCard
            icon={<Calendar className="w-5 h-5" />}
            label="Founded"
            value={companyInfo.founded_year.toString()}
          />
        )}

        {/* Headquarters */}
        {companyInfo.headquarters && (
          <InfoCard
            icon={<MapPin className="w-5 h-5" />}
            label="Headquarters"
            value={companyInfo.headquarters}
          />
        )}

        {/* Processing Time */}
        {taskInfo.duration && (
          <InfoCard
            icon={<TrendingUp className="w-5 h-5" />}
            label="Processing Time"
            value={formatDuration(taskInfo.duration)}
          />
        )}
      </div>

      {/* Additional Data */}
      {companyInfo.additional_data && Object.keys(companyInfo.additional_data).length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Additional Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(companyInfo.additional_data).map(([key, value]) => (
              <div key={key} className="flex flex-col">
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                  {key.replace(/_/g, ' ')}
                </span>
                <span className="text-sm text-gray-900">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Metadata Footer */}
      <div className="bg-gray-50 rounded-lg p-4 text-xs text-gray-600">
        <div className="flex flex-wrap gap-4">
          <span>Task ID: {taskInfo.taskId}</span>
          {taskInfo.completedAt && (
            <span>Completed: {new Date(taskInfo.completedAt).toLocaleString()}</span>
          )}
          {taskInfo.duration && (
            <span>Duration: {formatDuration(taskInfo.duration)}</span>
          )}
        </div>
      </div>
    </div>
  );
}

// Helper Component
function InfoCard({
  icon,
  label,
  value
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-200 hover:shadow-md transition-shadow">
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
          {icon}
        </div>
        <span className="text-sm font-medium text-gray-600">{label}</span>
      </div>
      <div className="text-lg font-semibold text-gray-900">
        {value || 'N/A'}
      </div>
    </div>
  );
}
