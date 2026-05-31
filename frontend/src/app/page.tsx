"use client";

import React, { useState } from "react";
import { VideoUrlForm } from "../components/VideoUrlForm";
import { AnalysisSummary } from "../components/AnalysisSummary";
import { ChatBox } from "../components/ChatBox";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { VideoMetadata } from "../components/VideoCard";

export default function Home() {
  const [videoMetadata, setVideoMetadata] = useState<VideoMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (youtubeUrl: string, instagramUrl: string) => {
    setIsLoading(true);
    setError(null);
    setVideoMetadata([]);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          youtube_url: youtubeUrl,
          instagram_url: instagramUrl,
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => null);
        throw new Error(errData?.detail || "Failed to analyze video URLs. Check if URLs are correct.");
      }

      const data = await response.json();
      setVideoMetadata(data);
    } catch (err: any) {
      console.error("Analysis error:", err);
      setError(
        err.message || "Could not connect to the API backend. Please ensure the FastAPI server is running on localhost:8000."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col items-center justify-between font-sans selection:bg-violet-500/30 relative overflow-hidden pb-12">
      {/* Decorative Background Gradients */}
      <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-violet-900/10 blur-[150px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[650px] h-[650px] rounded-full bg-indigo-900/10 blur-[150px] pointer-events-none" />
      <div className="absolute top-[30%] right-[15%] w-[400px] h-[400px] rounded-full bg-fuchsia-900/5 blur-[120px] pointer-events-none" />

      {/* Main Header / Nav */}
      <header className="w-full max-w-6xl px-6 py-6 flex items-center justify-between border-b border-zinc-900/80 backdrop-blur-md z-10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-tr from-violet-600 to-indigo-600 rounded-xl shadow-lg border border-violet-500/20">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-white via-zinc-200 to-zinc-400">
              VibeAnalyzer
            </h1>
            <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">
              AI Performance Suite
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
          <span className="text-xs text-zinc-400 font-semibold font-mono">FastAPI API Connected</span>
        </div>
      </header>

      {/* Main Dashboard Layout */}
      <main className="w-full max-w-5xl px-6 py-12 flex flex-col gap-10 z-10 flex-1">
        {/* Title Hero Section */}
        <section className="text-center md:text-left space-y-3">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-none">
            AI-Powered Video Performance Analyst
          </h2>
          <p className="text-zinc-400 text-base sm:text-lg max-w-2xl leading-relaxed">
            Compare performance metrics, analyze transcript storytelling, evaluate hook quality, and identify suggestions for YouTube and Instagram Reels side by side.
          </p>
        </section>

        {/* Video URL Form Section */}
        <section className="space-y-4">
          <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest">
            1. Input Video Sources
          </h3>
          <VideoUrlForm onAnalyze={handleAnalyze} isLoading={isLoading} />
        </section>

        {/* Error Feedback */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 p-4 rounded-xl flex gap-3 items-start animate-shake">
            <svg className="w-5 h-5 text-red-400 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="text-sm">
              <h4 className="font-bold text-red-200">Analysis Error Encountered</h4>
              <p className="text-red-400/90 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Video Analysis Summary Section */}
        {(isLoading || videoMetadata.length > 0) && (
          <section className="space-y-4">
            <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest">
              2. Video Performance Comparisons
            </h3>
            {isLoading ? <LoadingSkeleton /> : <AnalysisSummary videos={videoMetadata} />}
          </section>
        )}

        {/* AI Chat Section */}
        <section className="space-y-4">
          <h3 className="text-sm font-bold text-zinc-400 uppercase tracking-widest">
            3. AI Assistant Deep-Dive
          </h3>
          <ChatBox videoMetadata={videoMetadata} disabled={videoMetadata.length === 0 || isLoading} />
        </section>
      </main>

      {/* Footer */}
      <footer className="w-full max-w-6xl px-6 pt-12 border-t border-zinc-900/60 flex flex-col sm:flex-row items-center justify-between text-zinc-600 text-xs gap-4 z-10">
        <p>© 2026 VibeAnalyzer. Built with Next.js, LangGraph, and Qdrant.</p>
        <div className="flex gap-4">
          <span className="hover:text-zinc-400 transition-colors">Documentation</span>
          <span className="hover:text-zinc-400 transition-colors">GitHub</span>
          <span className="hover:text-zinc-400 transition-colors">Developer Portal</span>
        </div>
      </footer>
    </div>
  );
}
