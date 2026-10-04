import { Calendar, MapPin, Users, Quote, Sparkles, Play, GitCompare } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function MemoryCard({ memory, onPlayAudio }) {
  const navigate = useNavigate();

  const handlePlayAudio = (time = null) => {
    const audioId = memory.audio_id || memory.memory_id;
    const rawStart = time !== null ? time : (memory.start_time || 0);
    const startTime = Math.max(0, parseFloat(rawStart) || 0);
    if (onPlayAudio && audioId) {
      onPlayAudio({
        audioId,
        startTime,
        title: memory.title
      });
    }
  };

  const formatSec = (s) => `${Math.floor(s / 60)}:${Math.floor(s % 60).toString().padStart(2, '0')}`;
  const startT = Math.max(0, parseFloat(memory.start_time) || 0);
  const endT = Math.max(0, parseFloat(memory.end_time) || 0);
  const hasTimeRange = endT > startT;

  return (
    <div className="glass-panel rounded-2xl p-6 border border-slate-800 hover:border-amber-500/40 transition-all duration-300 shadow-xl group flex flex-col justify-between">
      <div>
        {/* Header & Badges */}
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
          <div className="flex flex-wrap items-center gap-2 text-xs font-medium text-amber-400">
            <span className="flex items-center space-x-1 bg-amber-500/10 px-2.5 py-1 rounded-full border border-amber-500/20">
              <Calendar className="w-3 h-3" />
              <span>{memory.time_period || 'Timeless'}</span>
            </span>
            {memory.location && memory.location !== 'Unspecified' && (
              <span className="flex items-center space-x-1 bg-slate-800/80 px-2.5 py-1 rounded-full text-slate-300 border border-slate-700">
                <MapPin className="w-3 h-3" />
                <span>{memory.location}</span>
              </span>
            )}
            {hasTimeRange ? (
              <span className="text-[10px] font-mono bg-slate-900/80 text-amber-400/90 px-2 py-0.5 rounded border border-amber-500/20">
                {formatSec(startT)} - {formatSec(endT)}
              </span>
            ) : startT > 0 ? (
              <span className="text-[10px] font-mono bg-slate-900/80 text-amber-400/90 px-2 py-0.5 rounded border border-amber-500/20">
                Starts at {formatSec(startT)}
              </span>
            ) : null}
          </div>


          <div className="flex items-center space-x-2">
            <button
              onClick={() => handlePlayAudio(startT)}
              className="flex items-center space-x-1.5 text-xs text-slate-950 font-bold bg-amber-400 hover:bg-amber-300 px-3 py-1 rounded-lg transition shadow-md shadow-amber-500/10 cursor-pointer"
              title="Play original grandfather voice recording"
            >
              <Play className="w-3 h-3 fill-current" />
              <span>Play Voice</span>
            </button>
            <button
              onClick={() => navigate(`/compare?memoryId=${memory.id}`)}
              className="flex items-center space-x-1 text-xs text-amber-400 hover:text-amber-300 transition bg-amber-950/40 hover:bg-amber-900/50 px-2.5 py-1 rounded-lg border border-amber-800/30 cursor-pointer"
            >
              <GitCompare className="w-3.5 h-3.5" />
              <span>Then vs Now</span>
            </button>
          </div>
        </div>

        {/* Title */}
        <h3 className="text-xl font-semibold text-white font-serif mb-2 group-hover:text-amber-200 transition-colors">
          {memory.title}
        </h3>

        {/* Summary */}
        <p className="text-sm text-slate-300 leading-relaxed mb-4">
          {memory.summary}
        </p>

        {/* Verbatim Quotes from Grandfather */}
        {memory.verbatim_quotes && memory.verbatim_quotes.length > 0 && (
          <div className="space-y-2 mb-4">
            {memory.verbatim_quotes.map((q, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-slate-900/70 border border-amber-900/20 flex items-start justify-between gap-3"
              >
                <div className="flex items-start space-x-2">
                  <Quote className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                  <p className="text-xs italic text-amber-100 font-serif">
                    "{q.quote || q}"
                  </p>
                </div>
                <button
                  onClick={() => handlePlayAudio(startT)}
                  title="Hear grandfather speak these exact words"
                  className="flex items-center space-x-1 text-[11px] font-medium text-amber-400 hover:text-amber-300 bg-amber-500/10 hover:bg-amber-500/20 px-2 py-1 rounded border border-amber-500/30 flex-shrink-0 cursor-pointer"
                >
                  <Play className="w-3 h-3 ml-0.5 fill-current" />
                  <span>Hear Voice</span>
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Life Advice Banner */}
        {memory.life_advice && (
          <div className="mb-4 p-3.5 rounded-xl bg-gradient-to-r from-amber-950/30 to-amber-900/20 border border-amber-600/30">
            <div className="flex items-center space-x-1.5 text-xs font-semibold text-amber-400 mb-1">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Grandfather's Wisdom</span>
            </div>
            <p className="text-xs text-amber-200/90 italic font-serif">
              "{memory.life_advice}"
            </p>
          </div>
        )}
      </div>

      {/* Footer: Tags & People */}
      <div className="flex flex-wrap items-center gap-1.5 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400">
        {memory.people_mentioned && memory.people_mentioned.length > 0 && (
          <div className="flex items-center space-x-1 text-slate-400 mr-2">
            <Users className="w-3 h-3 text-slate-500" />
            <span>{memory.people_mentioned.join(', ')}</span>
          </div>
        )}
        {memory.tags && memory.tags.map((tag, i) => (
          <span key={i} className="bg-slate-800 px-2 py-0.5 rounded text-slate-400">
            #{tag}
          </span>
        ))}
      </div>
    </div>
  );
}
