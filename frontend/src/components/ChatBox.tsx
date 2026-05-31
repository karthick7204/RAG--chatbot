import React, { useState, useRef, useEffect } from "react";
import { ChatMessage, Message } from "./ChatMessage";
import { VideoMetadata } from "./VideoCard";

interface ChatBoxProps {
  videoMetadata: VideoMetadata[];
  disabled: boolean;
}

export const ChatBox: React.FC<ChatBoxProps> = ({ videoMetadata, disabled }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      sender: "assistant",
      text: "👋 Welcome to the AI Video Analyst! I've loaded your video transcripts and performance metrics. Ask me any comparison questions, like analyzing hooks, engagement metrics, CTAs, storytelling, or asking for improvements.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const suggestionQuestions = [
    "Why did Video A perform better?",
    "Compare the hooks.",
    "Suggest improvements.",
    "Analyze storytelling.",
  ];

  const handleSend = async (textToSend: string) => {
    if (!textToSend.trim() || isStreaming || disabled) return;

    const userMessage: Message = {
      id: Math.random().toString(),
      sender: "user",
      text: textToSend,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsStreaming(true);

    const aiMessageId = Math.random().toString();
    // Add placeholder AI message
    setMessages((prev) => [
      ...prev,
      { id: aiMessageId, sender: "assistant", text: "Thinking..." },
    ]);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: textToSend,
          video_metadata: videoMetadata,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || "Failed to generate chat response.");
      }

      if (!response.body) {
        throw new Error("No response body available for streaming.");
      }

      // Reset AI message placeholder before streaming content
      setMessages((prev) =>
        prev.map((m) => (m.id === aiMessageId ? { ...m, text: "" } : m))
      );

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          const chunkValue = decoder.decode(value);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === aiMessageId ? { ...m, text: m.text + chunkValue } : m
            )
          );
        }
      }
    } catch (err: any) {
      console.error("Chat error:", err);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMessageId
            ? {
                ...m,
                text: `⚠️ Error: ${err.message || "Failed to retrieve answer from the assistant. Make sure the backend is running."}`,
              }
            : m
        )
      );
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend(input);
    }
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl flex flex-col h-[550px] shadow-xl w-full overflow-hidden relative">
      {/* Glow header highlight */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-violet-500 via-fuchsia-500 to-indigo-500" />

      {/* Chat Header */}
      <div className="px-6 py-4 border-b border-zinc-800 bg-zinc-900/60 backdrop-blur-sm flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-ping" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            AI Video Performance Chat Assistant
          </h3>
        </div>
        <span className="text-xs text-zinc-500">
          Comparing {videoMetadata.length} Videos
        </span>
      </div>

      {/* Messages Scroll Area */}
      <div
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto px-6 py-6 space-y-4 bg-zinc-950/20 scrollbar-thin scrollbar-thumb-zinc-800"
      >
        {messages.map((m) => (
          <ChatMessage key={m.id} message={m} />
        ))}
        {/* Scroll target */}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggestion Chips */}
      {messages.length === 1 && !disabled && (
        <div className="px-6 py-2 bg-zinc-900/40 border-t border-zinc-800/50 flex flex-wrap gap-2">
          {suggestionQuestions.map((q, idx) => (
            <button
              key={idx}
              type="button"
              disabled={isStreaming}
              onClick={() => handleSend(q)}
              className="text-xs bg-zinc-950 hover:bg-zinc-850 text-zinc-400 hover:text-white border border-zinc-800 hover:border-zinc-700 font-semibold px-3 py-1.5 rounded-full transition-all duration-200 cursor-pointer"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Chat Input form */}
      <div className="p-4 border-t border-zinc-800 bg-zinc-900/80 backdrop-blur-sm flex gap-3">
        <input
          type="text"
          placeholder={
            disabled
              ? "Analyze videos first to unlock the AI Chat assistant..."
              : isStreaming
                ? "Streaming AI analysis response..."
                : "Ask a question about hooks, metrics, CTR, storytelling, or suggestions..."
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          disabled={disabled || isStreaming}
          className="flex-1 bg-zinc-950 border border-zinc-800 focus:border-zinc-700 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <button
          type="button"
          onClick={() => handleSend(input)}
          disabled={disabled || isStreaming || !input.trim()}
          className={`px-5 py-3 rounded-xl font-bold transition-all flex items-center justify-center gap-1.5 shadow-md ${
            disabled || isStreaming || !input.trim()
              ? "bg-zinc-800 text-zinc-600 cursor-not-allowed border border-zinc-700/50"
              : "bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white cursor-pointer active:scale-95"
          }`}
        >
          {isStreaming ? (
            <span className="w-5 h-5 border-2 border-zinc-400 border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              Send
              <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
              </svg>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
