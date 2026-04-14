import { useState, useRef, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";
import { EraAvatar } from "./EraAvatar";
import { EraPet } from "./EraPet";

interface Message {
  role: "user" | "era";
  text: string;
  suggestions?: string[];
}

export function EraChatWidget() {
  const location = useLocation();
  const match = location.pathname.match(/\/spaces\/([^/]+)/);
  const spaceKey = match ? match[1] : undefined;
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    { role: "era", text: "Hi! I'm ERA, your AI project assistant. How can I help?", suggestions: ["Project status", "Show all items", "Help"] },
  ]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const { data: suggestionsData } = useQuery({
    queryKey: ["era-suggestions", spaceKey],
    queryFn: async () => {
      const res = await api.get("/ai/suggestions", { params: { space_key: spaceKey } });
      return res.data.data.suggestions as string[];
    },
    enabled: isAuthenticated && open && !!spaceKey,
    refetchInterval: 60000,
  });

  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      const res = await api.post("/ai/chat", { message, space_key: spaceKey || undefined });
      return res.data.data as { reply: string; suggestions: string[] };
    },
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { role: "era", text: data.reply, suggestions: data.suggestions },
      ]);
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        { role: "era", text: "Sorry, I couldn't process that. Try again." },
      ]);
    },
  });

  const handleSend = (text?: string) => {
    const msg = text || input.trim();
    if (!msg) return;
    setMessages((prev) => [...prev, { role: "user", text: msg }]);
    setInput("");
    chatMutation.mutate(msg);
  };

  if (!isAuthenticated) return null;

  return (
    <>
      {/* Strolling pet — visible when chat is closed */}
      <EraPet
        onChatOpen={() => setOpen(true)}
        isChatOpen={open}
        isThinking={chatMutation.isPending}
        isSpeaking={false}
      />

      {/* Chat panel */}
      {open && (
        <div className="fixed bottom-6 right-6 z-40 w-96 h-[32rem] rounded-xl border border-slate-200 bg-white shadow-2xl flex flex-col overflow-hidden">
          {/* Header */}
          <div className="bg-brand-navy px-4 py-3 flex items-center gap-3 flex-shrink-0">
            <EraAvatar size={32} speaking={chatMutation.isPending} thinking={chatMutation.isPending} />
            <div className="flex-1">
              <p className="text-sm font-semibold text-white">ERA AI</p>
              <p className="text-[10px] text-slate-400">
                {chatMutation.isPending ? "Thinking..." : "Online — real project data"}
              </p>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="text-slate-400 hover:text-white transition-colors"
              aria-label="Close chat"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
            {suggestionsData && suggestionsData.length > 0 && messages.length <= 1 && (
              <div className="bg-amber-50 border border-amber-200 rounded-md p-2">
                <p className="text-[10px] text-amber-600 font-medium mb-1">Alerts:</p>
                {suggestionsData.map((s, i) => (
                  <button key={i} onClick={() => handleSend(s)}
                    className="block text-xs text-amber-700 hover:underline text-left">
                    {s}
                  </button>
                ))}
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[85%] ${
                  msg.role === "user"
                    ? "bg-brand-blue text-white rounded-2xl rounded-br-md px-3 py-2"
                    : "bg-surface-tertiary text-text-primary rounded-2xl rounded-bl-md px-3 py-2"
                }`}>
                  <div className="text-sm whitespace-pre-wrap"
                    dangerouslySetInnerHTML={{
                      __html: msg.text
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/\n/g, '<br/>'),
                    }}
                  />
                  {msg.suggestions && msg.suggestions.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {msg.suggestions.map((s, j) => (
                        <button key={j} onClick={() => handleSend(s)}
                          className={`rounded-full border px-2 py-0.5 text-[10px] transition-colors ${
                            msg.role === "user"
                              ? "border-white/20 hover:bg-white/20"
                              : "border-slate-200 bg-white hover:bg-slate-50 text-text-secondary"
                          }`}>
                          {s}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {chatMutation.isPending && (
              <div className="flex justify-start">
                <div className="bg-surface-tertiary rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex gap-1">
                    <span className="h-2 w-2 rounded-full bg-brand-sky animate-bounce" style={{ animationDelay: "0s" }} />
                    <span className="h-2 w-2 rounded-full bg-brand-sky animate-bounce" style={{ animationDelay: "0.15s" }} />
                    <span className="h-2 w-2 rounded-full bg-brand-sky animate-bounce" style={{ animationDelay: "0.3s" }} />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <form
            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
            className="border-t border-slate-200 px-3 py-2 flex gap-2 flex-shrink-0"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask ERA anything..."
              className="flex-1 rounded-full border border-slate-200 px-3 py-1.5 text-sm focus:ring-2 focus:ring-brand-sky focus:border-brand-sky outline-none"
              disabled={chatMutation.isPending}
            />
            <button
              type="submit"
              disabled={chatMutation.isPending || !input.trim()}
              className="rounded-full bg-brand-blue w-8 h-8 flex items-center justify-center text-white hover:bg-brand-blue/90 transition-colors disabled:opacity-50"
              aria-label="Send"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
          </form>
        </div>
      )}
    </>
  );
}
