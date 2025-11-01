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
  TrendingUp,
  Facebook,
  Linkedin,
  Mail,
  Home
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
                Legal Name: <span className="font-medium">{companyInfo.legal_name}</span>
              </p>
            )}

            {/* SEO Description */}
            {companyInfo.seo_description && (
              <p className="text-sm text-gray-700 mt-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
                {companyInfo.seo_description}
              </p>
            )}

            {/* Full Description */}
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
        <div className="mt-6 flex flex-wrap gap-3">
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
              <Linkedin className="w-4 h-4" />
              LinkedIn
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
          {companyInfo.facebook_url && (
            <a
              href={companyInfo.facebook_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-[#1877F2] text-white rounded-lg hover:bg-[#145dbf] transition-colors"
            >
              <Facebook className="w-4 h-4" />
              Facebook
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
              <div>
                {companyInfo.employee_count && (
                  <div className="font-semibold">{formatNumber(companyInfo.employee_count)}+</div>
                )}
                {companyInfo.employee_range && (
                  <div className="text-sm text-gray-600">Range: {companyInfo.employee_range}</div>
                )}
              </div>
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

      {/* Detailed Address Section */}
      {(companyInfo.full_address || companyInfo.street_address || companyInfo.city) && (
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
          <div className="flex items-center gap-2 mb-4">
            <Home className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">Address Details</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {companyInfo.full_address && (
              <div className="col-span-2">
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-1">
                  Full Address
                </span>
                <span className="text-sm text-gray-900">{companyInfo.full_address}</span>
              </div>
            )}

            {companyInfo.street_address && (
              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-1">
                  Street Address
                </span>
                <span className="text-sm text-gray-900">{companyInfo.street_address}</span>
              </div>
            )}

            {companyInfo.city && (
              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-1">
                  City
                </span>
                <span className="text-sm text-gray-900">{companyInfo.city}</span>
              </div>
            )}

            {companyInfo.state && (
              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-1">
                  State/Province
                </span>
                <span className="text-sm text-gray-900">{companyInfo.state}</span>
              </div>
            )}

            {companyInfo.country && (
              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-1">
                  Country
                </span>
                <span className="text-sm text-gray-900">{companyInfo.country}</span>
              </div>
            )}

            {companyInfo.postal_code && (
              <div>
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide block mb-1">
                  Postal Code
                </span>
                <span className="text-sm text-gray-900">{companyInfo.postal_code}</span>
              </div>
            )}
          </div>
        </div>
      )}

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

      {/* Data Sources */}
      {companyInfo.sources && companyInfo.sources.length > 0 && (
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl shadow-lg p-6 border border-blue-200">
          <div className="flex items-center gap-2 mb-4">
            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <h3 className="text-lg font-semibold text-gray-900">Data Sources</h3>
            <span className="ml-2 px-2 py-1 text-xs font-medium bg-blue-600 text-white rounded-full">
              {companyInfo.sources.length}
            </span>
          </div>

          <p className="text-sm text-gray-600 mb-4">
            Information gathered from {companyInfo.sources.length} verified source{companyInfo.sources.length !== 1 ? 's' : ''}
          </p>

          <div className="grid grid-cols-1 gap-3">
            {companyInfo.sources.map((source, index) => {
              // Extract domain name from URL for display
              let displayName = source;
              let favicon = null;

              try {
                const url = new URL(source);
                displayName = url.hostname.replace('www.', '');
                favicon = `https://www.google.com/s2/favicons?domain=${url.hostname}&sz=32`;
              } catch (e) {
                // If URL parsing fails, use source as-is
              }

              return (
                <a
                  key={index}
                  href={source}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200 hover:border-blue-400 hover:shadow-md transition-all duration-200"
                >
                  {/* Favicon */}
                  {favicon && (
                    <img
                      src={favicon}
                      alt=""
                      className="w-5 h-5 flex-shrink-0"
                      onError={(e) => {
                        // Hide image if favicon fails to load
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  )}

                  {/* Source info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900 truncate">
                        {displayName}
                      </span>
                      <ExternalLink className="w-3 h-3 text-gray-400 group-hover:text-blue-600 flex-shrink-0" />
                    </div>
                    <span className="text-xs text-gray-500 truncate block">
                      {source}
                    </span>
                  </div>

                  {/* Arrow indicator */}
                  <svg
                    className="w-5 h-5 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </a>
              );
            })}
          </div>

          {/* Source reliability note */}
          <div className="mt-4 pt-4 border-t border-blue-200">
            <p className="text-xs text-gray-600 flex items-start gap-2">
              <svg className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <span>
                Data aggregated from public sources including company websites, business directories, and professional networks.
                Verify critical information directly with the company.
              </span>
            </p>
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
