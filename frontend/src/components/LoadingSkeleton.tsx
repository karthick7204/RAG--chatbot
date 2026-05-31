import React from "react";

export const LoadingSkeleton: React.FC = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full animate-pulse">
      {[1, 2].map((i) => (
        <div
          key={i}
          className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden shadow-xl"
        >
          {/* Thumbnail Skeleton */}
          <div className="w-full aspect-video bg-zinc-800" />
          
          <div className="p-6 space-y-4">
            {/* Title & Creator */}
            <div className="space-y-2">
              <div className="h-6 bg-zinc-800 rounded-lg w-3/4" />
              <div className="h-4 bg-zinc-800 rounded-lg w-1/2" />
            </div>
            
            {/* Divider */}
            <div className="border-t border-zinc-800 pt-4" />
            
            {/* Metrics Grid */}
            <div className="grid grid-cols-3 gap-4">
              {[1, 2, 3].map((m) => (
                <div key={m} className="space-y-2 text-center">
                  <div className="h-4 bg-zinc-800 rounded-lg w-1/2 mx-auto" />
                  <div className="h-6 bg-zinc-800 rounded-lg w-3/4 mx-auto" />
                </div>
              ))}
            </div>

            {/* Engagement Rate */}
            <div className="bg-zinc-950/50 p-4 rounded-xl border border-zinc-800/50 mt-4 flex items-center justify-between">
              <div className="h-4 bg-zinc-800 rounded-lg w-1/3" />
              <div className="h-6 bg-zinc-800 rounded-lg w-1/6" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
