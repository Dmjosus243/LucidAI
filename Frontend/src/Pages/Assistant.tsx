import { useEffect, useRef, useState } from "react";
import { Layout } from "../Components/Layout";
import {
  createChatSession,
  getChatSessions,
  getChatMessages,
  sendChatMessage,
} from "../Services/api";
import type { ChatSessionItem, ChatMessageItem } from "../Services/api";

export const Assistant = () => {
  const [sessions, setSessions] = useState<ChatSessionItem[]>([]);
  const [currentSession, setCurrentSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  const loadSessions = () => {
    getChatSessions().then((res) => setSessions(res.data)).finally(() => setLoadingSessions(false));
  };

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const startNewChat = () => {
    setCurrentSession(null);
    setMessages([]);
    setInput("");
  };

  const selectSession = (id: string) => {
    setCurrentSession(id);
    getChatMessages(id).then((res) => setMessages(res.data)).catch(() => {});
  };

  const handleSend = async () => {
    const content = input.trim();
    if (!content || sending) return;
    setInput("");
    setSending(true);

    let sessionId = currentSession;
    if (!sessionId) {
      try {
        const created = await createChatSession();
        sessionId = created.data.id;
        setCurrentSession(sessionId);
        setSessions((prev) => [created.data, ...prev]);
      } catch {
        setSending(false);
        return;
      }
    }

    // affichage optimiste
    setMessages((prev) => [
      ...prev,
      { id: `opt-${Date.now()}`, role: "user", content },
    ]);
    try {
      const res = await sendChatMessage(sessionId, content);
      setMessages((prev) => [
        ...prev.filter((m) => !m.id.startsWith("opt-")),
        res.data.user_message,
        res.data.assistant_message,
      ]);
    } catch {
      setSending(false);
    }
    setSending(false);
  };

  return (
    <Layout>
      <div className="mb-6">
        <h1 className="page-title">Assistant</h1>
        <p className="text-gray-500 text-sm mt-1">
          Interrogez vos données d'audit en langage naturel.
        </p>
      </div>

      <div className="card overflow-hidden">
        <div className="flex flex-col md:flex-row" style={{ minHeight: "60vh" }}>
          {/* Liste des sessions */}
          <div className="w-full md:w-64 shrink-0 border-b md:border-b-0 md:border-r border-white/10 p-4">
            <button onClick={startNewChat} className="btn-primary w-full mb-4 text-sm">
              + Nouvelle conversation
            </button>
            <div className="space-y-1">
              {loadingSessions && <p className="text-xs text-gray-500">Chargement...</p>}
              {!loadingSessions && sessions.length === 0 && (
                <p className="text-xs text-gray-500">Aucune conversation.</p>
              )}
              {sessions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => selectSession(s.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                    currentSession === s.id
                      ? "bg-cyan-500/15 text-cyan-300"
                      : "text-gray-300 hover:bg-white/5"
                  }`}
                >
                  <p className="truncate">{s.title}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Fenêtre de chat */}
          <div className="flex-1 flex flex-col">
            <div className="flex-1 overflow-y-auto p-5 space-y-4" style={{ maxHeight: "60vh" }}>
              {messages.length === 0 && (
                <div className="text-center py-16 text-gray-500">
                  <p className="text-4xl mb-3">💬</p>
                  <p className="text-cyan-300 font-semibold">Posez une question à l'assistant</p>
                  <p className="text-sm mt-2 text-gray-500">
                    Ex. : « combien d'écritures ai-je ? », « quel est mon niveau de risque ? »
                  </p>
                </div>
              )}
              {messages.map((m) => (
                <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${
                      m.role === "user"
                        ? "bg-cyan-500/20 text-white border border-cyan-500/20"
                        : "bg-white/[0.04] text-gray-200 border border-white/10"
                    }`}
                  >
                    <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
                    {m.mode === "local" && (
                      <p className="text-[10px] text-gray-500 mt-2">Réponse locale (mode hors-ligne)</p>
                    )}
                  </div>
                </div>
              ))}
              {sending && (
                <div className="flex justify-start">
                  <div className="bg-white/[0.04] border border-white/10 rounded-2xl px-4 py-3 text-sm text-gray-400">
                    Réflexion...
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            <div className="border-t border-white/10 p-4">
              <div className="flex items-center gap-2">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSend()}
                  placeholder="Écrivez votre question..."
                  className="input flex-1"
                  disabled={sending}
                />
                <button onClick={handleSend} disabled={sending || !input.trim()} className="btn-primary">
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};
