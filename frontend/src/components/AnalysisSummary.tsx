import React from "react";
import { VideoCard, VideoMetadata } from "./VideoCard";

interface AnalysisSummaryProps {
  videos: VideoMetadata[];
}

export const AnalysisSummary: React.FC<AnalysisSummaryProps> = ({ videos }) => {
  if (videos.length < 2) return null;

  const videoA = videos[0];
  const videoB = videos[1];

  // Derive comparison metrics
  const erA = videoA.engagement_rate || 0;
  const erB = videoB.engagement_rate || 0;
  
  const betterEngagement = erA > erB ? "Video A" : erB > erA ? "Video B" : "Draw";
  const engagementDiff = Math.abs(erA - erB).toFixed(2);

  const viewsA = videoA.views || 0;
  const viewsB = videoB.views || 0;
  const betterViews = viewsA > viewsB ? "Video A" : viewsB > viewsA ? "Video B" : "Draw";
  const viewsDiff = Math.abs(viewsA - viewsB).toLocaleString();

  return (
    <div className="space-y-8 w-full">
      {/* Comparison Insight Panel */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        {/* Glow decoration */}
        <div className="absolute -right-24 -top-24 w-48 h-48 rounded-full bg-violet-600/10 blur-3xl pointer-events-none" />
        <div className="absolute -left-24 -bottom-24 w-48 h-48 rounded-full bg-emerald-600/5 blur-3xl pointer-events-none" />

        <h3 className="text-sm font-semibold text-zinc-500 uppercase tracking-widest mb-4">
          Performance Insights
        </h3>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div className="flex items-center gap-4 bg-zinc-950/40 p-4 rounded-xl border border-zinc-800/50">
            <div className="p-3 bg-violet-500/10 rounded-xl border border-violet-500/20 text-violet-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <span className="block text-xs text-zinc-400 font-medium">Higher Engagement Rate</span>
              <span className="text-lg font-bold text-white">
                {betterEngagement === "Draw" ? (
                  "Draw"
                ) : (
                  <>
                    {betterEngagement} <span className="text-violet-400 text-sm ml-1.5">(+{engagementDiff}%)</span>
                  </>
                )}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4 bg-zinc-950/40 p-4 rounded-xl border border-zinc-800/50">
            <div className="p-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20 text-emerald-400">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </div>
            <div>
              <span className="block text-xs text-zinc-400 font-medium">Higher View Count</span>
              <span className="text-lg font-bold text-white">
                {betterViews === "Draw" ? (
                  "Draw"
                ) : (
                  <>
                    {betterViews} <span className="text-emerald-400 text-sm ml-1.5">(+{viewsDiff} views)</span>
                  </>
                )}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Video Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full">
        <VideoCard video={videoA} label="Video A (YouTube)" />
        <VideoCard video={videoB} label="Video B (Instagram)" />
      </div>
    </div>
  );
};
