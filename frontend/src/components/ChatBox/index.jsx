import { useState } from 'react';
import { Send, Sparkles, ShieldCheck, Play, Loader2 } from 'lucide-react';
import { api } from '../../services/api';

export default function ChatBox({ onPlayAudio }) {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([
    {
      sender: 'system',
      text: "Ask me anything about grandfather's life, stories, or advice. Every answer is grounded strictly in his authentic recorded voice.",
      citations: []
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!question.trim() || isLoading) return;

    const userText = question.trim();
    setQuestion('');
    setMessages((prev) => [...prev, { sender: 'user', text: userText }]);
    setIsLoading(true);

    try {
      const data = await api.askGrandfather(userText);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: data.answer,
          sources: data.sources || data.citations || [],
          citations: data.sources || data.citations || [],
          grounded: data.grounded
        }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: "I couldn't search grandfather's memories at the moment. Please verify the backend and Ollama services are running.",
          isError: true
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="glass-panel rounded-2xl flex flex-col h-[650px] border border-slate-800 shadow-2xl overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Ask Grandfather's Archive</h3>
            <p className="text-[11px] text-slate-400">Strictly answers from his recorded words</p>
          </div>
        </div>

        <div className="flex items-center space-x-1 bg-emerald-500/10 text-emerald-400 text-[11px] font-medium px-2.5 py-1 rounded-full border border-emerald-500/20">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Zero Hallucination Guarantee</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 p-5 overflow-y-auto space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed ${msg.sender === 'user'
                ? 'bg-amber-600 text-white rounded-br-none shadow-lg shadow-amber-900/20'
                : 'bg-slate-900/90 text-slate-200 border border-slate-800 rounded-bl-none shadow-md'
                }`}
            >
              <p className="whitespace-pre-wrap">{msg.text}</p>

              {/* Grounded Sources & Audio playback triggers */}
              {((msg.sources && msg.sources.length > 0) || (msg.citations && msg.citations.length > 0)) && (
                <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-2">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-amber-400/90 block">
                    Recorded Voice Sources & Citations:
                  </span>
                  {(msg.sources || msg.citations).map((cite, cIdx) => {
                    const startTime = Math.max(0, parseFloat(cite.start_time ?? cite.timestamp_start ?? 0) || 0);
                    const endTime = Math.max(0, parseFloat(cite.end_time ?? cite.timestamp_end ?? 0) || 0);
                    const formatSec = (s) => `${Math.floor(s / 60)}:${Math.floor(s % 60).toString().padStart(2, '0')}`;
                    const timeBadge = (endTime > startTime)
                      ? `${formatSec(startTime)} - ${formatSec(endTime)}`
                      : (startTime > 0 ? `Starts at ${formatSec(startTime)}` : 'Full Story');


                    return (
                      <div
                        key={cIdx}
                        className="bg-slate-950/70 p-3 rounded-xl border border-amber-900/30 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <span className="font-semibold text-amber-200">
                              {cite.title || cite.memory_title}
                            </span>
                            <span className="text-[10px] bg-amber-500/10 text-amber-400 px-1.5 py-0.5 rounded font-mono border border-amber-500/20">
                              {timeBadge}
                            </span>
                          </div>
                          {(cite.verbatim_quote || cite.quote) && (
                            <p className="text-[11px] italic text-slate-300 line-clamp-2">
                              "{cite.verbatim_quote || cite.quote}"
                            </p>
                          )}
                          {cite.audio_source && (
                            <p className="text-[10px] text-slate-500 font-mono">
                              Source: {cite.audio_source}
                            </p>
                          )}
                        </div>
                        <button
                          onClick={() =>
                            onPlayAudio &&
                            onPlayAudio({
                              audioId: cite.audio_id || cite.memory_id,
                              startTime: startTime,
                              title: cite.title || cite.memory_title
                            })
                          }
                          className="inline-flex items-center justify-center space-x-1.5 text-xs font-medium text-slate-950 bg-amber-400 hover:bg-amber-300 px-3 py-1.5 rounded-lg transition shadow-md shadow-amber-500/10 flex-shrink-0"
                          title="Play original recording at exact timestamp"
                        >
                          <Play className="w-3.5 h-3.5 fill-current" />
                          <span>Play original recording</span>
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center space-x-2 text-xs text-amber-400/80 bg-slate-900/60 p-3 rounded-xl border border-slate-800 w-fit">
            <Loader2 className="w-4 h-4 animate-spin text-amber-500" />
            <span>Consulting grandfather's authentic recordings...</span>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="p-4 border-t border-slate-800 bg-slate-900/60 flex items-center space-x-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. 'What was your first job?' or 'What advice did you have about hardship?'"
          className="flex-1 bg-slate-950 border border-slate-700 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition"
        />
        <button
          type="submit"
          disabled={!question.trim() || isLoading}
          className="p-2.5 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 rounded-xl transition shadow-lg shadow-amber-500/20 font-bold"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
