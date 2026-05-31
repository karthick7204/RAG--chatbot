import React from "react";

export interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
}

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === "user";

  // Simple Markdown parser for bold text (**text**), lists (* list or - list), and source links/citations
  const renderTextContent = (text: string) => {
    // If it's a source list section, split it and render it as badges
    const parts = text.split("\n");
    return parts.map((part, index) => {
      let line = part.trim();
      
      // Check if it's a bullet point
      const isBullet = line.startsWith("*") || line.startsWith("-");
      if (isBullet) {
        line = line.substring(1).trim();
      }

      // Format bold text (**text**)
      const boldRegex = /\*\*(.*?)\*\*/g;
      const elements: React.ReactNode[] = [];
      let lastIdx = 0;
      let match;

      while ((match = boldRegex.exec(line)) !== null) {
        const precedingText = line.substring(lastIdx, match.index);
        const boldText = match[1];
        
        if (precedingText) {
          elements.push(precedingText);
        }
        
        elements.push(
          <strong key={match.index} className="font-bold text-white">
            {boldText}
          </strong>
        );
        
        lastIdx = boldRegex.lastIndex;
      }

      const remainingText = line.substring(lastIdx);
      if (remainingText) {
        // Highlight Video Chunks citations (e.g. videoA Chunk 1 or Video A Chunk 1)
        const chunkRegex = /(video[a-zA-Z0-9_]*\s+chunk\s+\d+|[a-zA-Z0-9_-]+_chunk_\d+)/i;
        const chunkMatch = remainingText.match(chunkRegex);
        if (chunkMatch) {
          const splitText = remainingText.split(chunkRegex);
          elements.push(
            <span key="rem">
              {splitText.map((chunkPart, i) => {
                if (chunkRegex.test(chunkPart)) {
                  return (
                    <span
                      key={i}
                      className="inline-flex items-center bg-violet-500/10 border border-violet-500/30 text-violet-400 text-xs px-2 py-0.5 rounded-md font-semibold font-mono"
                    >
                      {chunkPart}
                    </span>
                  );
                }
                return chunkPart;
              })}
            </span>
          );
        } else {
          elements.push(remainingText);
        }
      }

      if (isBullet) {
        return (
          <li key={index} className="ml-4 list-disc text-sm text-zinc-300 mb-1">
            {elements}
          </li>
        );
      }

      // Render Sources header differently
      if (line.toLowerCase().startsWith("sources:")) {
        return (
          <h4 key={index} className="text-xs font-bold uppercase tracking-wider text-zinc-500 mt-4 mb-2">
            Sources & References
          </h4>
        );
      }

      return (
        <p key={index} className="text-sm text-zinc-300 mb-2.5 leading-relaxed">
          {elements}
        </p>
      );
    });
  };

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-3 shadow-md border ${
          isUser
            ? "bg-violet-600 border-violet-700 text-white rounded-br-none"
            : "bg-zinc-900 border-zinc-800 text-zinc-200 rounded-bl-none"
        }`}
      >
        {/* Avatar label */}
        <div className="flex items-center gap-1.5 mb-1.5">
          {isUser ? (
            <span className="text-[10px] uppercase font-bold tracking-wider text-violet-200/80">
              You
            </span>
          ) : (
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-pulse" />
              <span className="text-[10px] uppercase font-bold tracking-wider text-violet-400">
                AI Analyst
              </span>
            </div>
          )}
        </div>

        {/* Message body */}
        <div className="space-y-0.5 select-text">
          {isUser ? (
            <p className="text-sm text-white font-medium leading-relaxed whitespace-pre-wrap">
              {message.text}
            </p>
          ) : (
            <div>{renderTextContent(message.text)}</div>
          )}
        </div>
      </div>
    </div>
  );
};
