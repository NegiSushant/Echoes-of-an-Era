import { Sparkles } from 'lucide-react';
import ChatBox from '../components/ChatBox';

export default function Ask({ onPlayAudio }) {
  return (
    <div className="space-y-6 pb-16">
      <div>
        <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 text-xs font-medium mb-2 border border-amber-500/20">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Grounded RAG Experience</span>
        </div>
        <h1 className="text-3xl font-bold font-serif text-white">Ask Grandfather</h1>
        <p className="text-sm text-slate-400 mt-1 max-w-xl">
          Consult his wisdom directly. The system searches across his lifetime recordings and provides direct voice timestamps for every statement.
        </p>
      </div>

      <ChatBox onPlayAudio={onPlayAudio} />
    </div>
  );
}
