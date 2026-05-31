import React from "react";

export interface VideoMetadata {
  platform: string;
  video_id: string;
  title: string;
  creator: string;
  followers?: number;
  views?: number;
  likes?: number;
  comments?: number;
  duration?: number;
  upload_date?: string;
  hashtags?: string[];
  description?: string;
  thumbnail?: string;
  engagement_rate?: number;
}

interface VideoCardProps {
  video: VideoMetadata;
  label: string; // "Video A" or "Video B"
}

export const VideoCard: React.FC<VideoCardProps> = ({ video, label }) => {
  const formatNumber = (num?: number) => {
    if (num === undefined || num === null) return "0";
    if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
    if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  const formatDuration = (sec?: number) => {
    if (!sec) return "0:00";
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  const isYouTube = video.platform?.toLowerCase() === "youtube";

  return (
    <div className="bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-2xl overflow-hidden shadow-xl transition-all duration-300 hover:scale-[1.01] flex flex-col h-full group">
      {/* Label and Platform Badge */}
      <div className="relative aspect-video w-full bg-zinc-950 overflow-hidden">
        {video.thumbnail ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={video.thumbnail}
            alt={video.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            onError={(e) => {
              // Fallback if image fails to load
              e.currentTarget.src =
                "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=500&auto=format&fit=crop";
            }}
          />
        ) : (
          <div className="w-full h-full bg-zinc-950 flex items-center justify-center">
            <svg
              className="w-12 h-12 text-zinc-800"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
          </div>
        )}

        {/* Video Label Badge (e.g. Video A) */}
        <div className="absolute top-4 left-4 bg-zinc-950/80 backdrop-blur-md text-white text-xs font-bold px-3 py-1.5 rounded-full border border-zinc-800 shadow-md">
          {label}
        </div>

        {/* Platform Badge */}
        <div className="absolute top-4 right-4 shadow-md">
          {isYouTube ? (
            <span className="bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-semibold px-3 py-1 rounded-full backdrop-blur-md flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse" />
              YouTube
            </span>
          ) : (
            <span className="bg-pink-500/10 border border-pink-500/30 text-pink-400 text-xs font-semibold px-3 py-1 rounded-full backdrop-blur-md flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-pink-500 rounded-full animate-pulse" />
              Instagram
            </span>
          )}
        </div>

        {/* Duration Badge */}
        {video.duration && (
          <div className="absolute bottom-4 right-4 bg-zinc-950/80 backdrop-blur-sm text-zinc-300 text-xs font-semibold px-2.5 py-1 rounded-md">
            {formatDuration(video.duration)}
          </div>
        )}
      </div>

      <div className="p-6 flex-1 flex flex-col justify-between">
        {/* Header Details */}
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-white line-clamp-2 leading-snug group-hover:text-violet-400 transition-colors">
            {video.title || "Untitled Video"}
          </h3>
          <div className="flex items-center justify-between text-sm text-zinc-400">
            <span className="font-medium hover:text-zinc-200 transition-colors">
              @{video.creator || "unknown"}
            </span>
            {video.followers !== undefined && video.followers > 0 && (
              <span>{formatNumber(video.followers)} followers</span>
            )}
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-zinc-800/80 my-4" />

        {/* Metrics Grid */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="bg-zinc-950/40 p-2.5 rounded-xl border border-zinc-800/40">
            <span className="block text-xs text-zinc-500 uppercase tracking-wider font-semibold mb-1">
              Views
            </span>
            <span className="text-base font-bold text-zinc-100">
              {formatNumber(video.views)}
            </span>
          </div>

          <div className="bg-zinc-950/40 p-2.5 rounded-xl border border-zinc-800/40">
            <span className="block text-xs text-zinc-500 uppercase tracking-wider font-semibold mb-1">
              Likes
            </span>
            <span className="text-base font-bold text-zinc-100">
              {formatNumber(video.likes)}
            </span>
          </div>

          <div className="bg-zinc-950/40 p-2.5 rounded-xl border border-zinc-800/40">
            <span className="block text-xs text-zinc-500 uppercase tracking-wider font-semibold mb-1">
              Comments
            </span>
            <span className="text-base font-bold text-zinc-100">
              {formatNumber(video.comments)}
            </span>
          </div>
        </div>

        {/* Engagement Rate Footer */}
        <div className="bg-zinc-950/60 p-4 rounded-xl border border-zinc-800/50 mt-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg
              className="w-4 h-4 text-violet-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
              />
            </svg>
            <span className="text-sm font-semibold text-zinc-400">Engagement</span>
          </div>
          <span className="text-lg font-bold text-violet-400">
            {video.engagement_rate !== undefined ? `${video.engagement_rate}%` : "N/A"}
          </span>
        </div>
      </div>
    </div>
  );
};
