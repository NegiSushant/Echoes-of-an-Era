import React from 'react';
import { Clock, Calendar, Volume2 } from 'lucide-react';
import MemoryCard from '../MemoryCard';

export default function Timeline({ memories = [], onPlayAudio }) {
  if (!memories.length) {
    return (
      <div className="glass-panel p-12 text-center rounded-2xl border border-slate-800">
        <Clock className="w-12 h-12 mx-auto text-amber-500/40 mb-3" />
        <h4 className="text-base font-semibold text-slate-300">No memories recorded yet</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          Deposit your grandfather's voice recording to begin charting his life timeline.
        </p>
      </div>
    );
  }

  return (
    <div className="relative pl-6 border-l-2 border-amber-600/30 space-y-8 my-6">
      {memories.map((mem, index) => (
        <div key={mem.id || index} className="relative group">
          {/* Timeline Dot */}
          <div className="absolute -left-[31px] top-6 w-4 h-4 rounded-full bg-slate-900 border-2 border-amber-500 group-hover:scale-125 transition-transform shadow-lg shadow-amber-500/30" />

          {/* Era Indicator */}
          <div className="mb-2 flex items-center space-x-2 text-xs font-semibold text-amber-400/90 font-mono">
            <Calendar className="w-3.5 h-3.5" />
            <span>{mem.time_period || 'Unspecified Decade'}</span>
          </div>

          <MemoryCard memory={mem} onPlayAudio={onPlayAudio} />
        </div>
      ))}
    </div>
  );
}
