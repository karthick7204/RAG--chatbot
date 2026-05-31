import React, { useState } from "react";

interface VideoUrlFormProps {
  onAnalyze: (youtubeUrl: string, instagramUrl: string) => Promise<void>;
  isLoading: boolean;
}

export const VideoUrlForm: React.FC<VideoUrlFormProps> = ({ onAnalyze, isLoading }) => {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [instagramUrl, setInstagramUrl] = useState("");
  const [errors, setErrors] = useState<{ youtube?: string; instagram?: string }>({});

  const validateUrls = (): boolean => {
    const newErrors: { youtube?: string; instagram?: string } = {};

    // Validate YouTube URL
    if (!youtubeUrl) {
      newErrors.youtube = "YouTube URL is required";
    } else {
      const ytPattern = /(youtube\.com|youtu\.be|youtube-nocookie\.com)/i;
      if (!ytPattern.test(youtubeUrl)) {
        newErrors.youtube = "Please enter a valid YouTube video or shorts URL";
      }
    }

    // Validate Instagram URL
    if (!instagramUrl) {
      newErrors.instagram = "Instagram Reel URL is required";
    } else {
      const igPattern = /instagram\.com/i;
      if (!igPattern.test(instagramUrl)) {
        newErrors.instagram = "Please enter a valid Instagram Reel URL";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateUrls() && !isLoading) {
      onAnalyze(youtubeUrl, instagramUrl);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 md:p-8 shadow-xl space-y-6 w-full relative overflow-hidden"
    >
      {/* Glow highlight */}
      <div className="absolute top-0 right-0 w-32 h-32 rounded-full bg-violet-600/5 blur-2xl pointer-events-none" />
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* YouTube Input Group */}
        <div className="space-y-2">
          <label
            htmlFor="youtube-url"
            className="block text-sm font-semibold text-zinc-300 flex items-center gap-2"
          >
            <svg
              className="w-4 h-4 text-red-500 fill-current"
              viewBox="0 0 24 24"
            >
              <path d="M23.498 6.163a3.003 3.003 0 0 0-2.11-2.11C19.518 3.545 12 3.545 12 3.545s-7.518 0-9.388.508a3.003 3.003 0 0 0-2.11 2.11C0 8.033 0 12 0 12s0 3.967.502 5.837a3.003 3.003 0 0 0 2.11 2.11c1.87.508 9.388.508 9.388.508s7.518 0 9.388-.508a3.003 3.003 0 0 0 2.11-2.11C24 15.967 24 12 24 12s0-3.967-.502-5.837zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
            </svg>
            YouTube Video or Shorts URL
          </label>
          <input
            id="youtube-url"
            type="text"
            placeholder="https://www.youtube.com/watch?v=..."
            value={youtubeUrl}
            onChange={(e) => {
              setYoutubeUrl(e.target.value);
              if (errors.youtube) {
                setErrors((prev) => ({ ...prev, youtube: undefined }));
              }
            }}
            disabled={isLoading}
            className={`w-full bg-zinc-950/80 border text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all ${
              errors.youtube ? "border-red-500/50" : "border-zinc-800 focus:border-zinc-700"
            }`}
          />
          {errors.youtube && (
            <p className="text-xs font-medium text-red-400 mt-1">{errors.youtube}</p>
          )}
        </div>

        {/* Instagram Input Group */}
        <div className="space-y-2">
          <label
            htmlFor="instagram-url"
            className="block text-sm font-semibold text-zinc-300 flex items-center gap-2"
          >
            <svg
              className="w-4 h-4 text-pink-500 fill-current"
              viewBox="0 0 24 24"
            >
              <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.051.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 0 0 0-12.324zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.406-11.845a1.44 1.44 0 1 0 0 2.881 1.44 1.44 0 0 0 0-2.881z" />
            </svg>
            Instagram Reel URL
          </label>
          <input
            id="instagram-url"
            type="text"
            placeholder="https://www.instagram.com/reel/..."
            value={instagramUrl}
            onChange={(e) => {
              setInstagramUrl(e.target.value);
              if (errors.instagram) {
                setErrors((prev) => ({ ...prev, instagram: undefined }));
              }
            }}
            disabled={isLoading}
            className={`w-full bg-zinc-950/80 border text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all ${
              errors.instagram ? "border-red-500/50" : "border-zinc-800 focus:border-zinc-700"
            }`}
          />
          {errors.instagram && (
            <p className="text-xs font-medium text-red-400 mt-1">{errors.instagram}</p>
          )}
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className={`w-full font-semibold py-3.5 px-6 rounded-xl text-white shadow-lg transition-all flex items-center justify-center gap-2.5 ${
          isLoading
            ? "bg-zinc-800 text-zinc-500 cursor-not-allowed border border-zinc-700/50"
            : "bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 active:scale-[0.99] cursor-pointer"
        }`}
      >
        {isLoading ? (
          <>
            <svg
              className="animate-spin -ml-1 mr-3 h-5 w-5 text-zinc-400"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Analyzing & Indexing Transcripts...
          </>
        ) : (
          <>
            <svg
              className="w-5 h-5 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2.5}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z"
              />
            </svg>
            Analyze Performance & Compare
          </>
        )}
      </button>
    </form>
  );
};
