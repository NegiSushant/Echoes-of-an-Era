import React, { useState, useEffect } from 'react';
import { History, ArrowRightLeft, Sparkles, MessageSquareHeart, HelpCircle, Loader2, Play, Volume2, Mic } from 'lucide-react';
import { api } from '../../services/api';

export default function ThenNow({ memoryId, query, topic, initialData, onPlayAudio }) {
  const [data, setData] = useState(initialData || null);
  const [isLoading, setIsLoading] = useState(!initialData && (!!memoryId || !!query || !!topic));
  const [error, setError] = useState(null);

  useEffect(() => {
    if ((memoryId || query || topic) && !initialData) {
      loadComparison();
    }
  }, [memoryId, query, topic]);

  const loadComparison = async () => {
    setIsLoading(true);
    setError(null);
    try {
      let res;
      if (memoryId) {
        res = await api.getOrGenerateComparison(memoryId);
      } else {
        res = await api.compareMemories({ query, topic });
      }
      setData(res);
    } catch (err) {
      setError(err.message || 'Could not generate Then vs Now comparison');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlaySource = () => {
    const audioId = data?.audio_id || data?.source_audio?.audio_id || data?.memory_id;
    const startTime = Math.max(0, parseFloat(data?.start_time ?? data?.source_audio?.start_time ?? 0) || 0);
    const title = data?.memory_title || data?.source_audio?.title || data?.topic;
    if (onPlayAudio && audioId) {
      onPlayAudio({ audioId, startTime, title });
    }
  };

  if (isLoading) {
    return (
      <div className="glass-panel p-12 rounded-2xl text-center border border-slate-800 space-y-3">
        <Loader2 className="w-8 h-8 animate-spin mx-auto text-amber-500" />
        <h4 className="text-sm font-semibold text-white">Analyzing Authentic Memories...</h4>
        <p className="text-xs text-slate-400">
          Comparing Grandfather's lived era with modern 2020s reality using Gemma 3.
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-panel p-6 rounded-2xl border border-red-900/40 text-center text-red-400 text-sm">
        {error}
      </div>
    );
  }

  if (!data) return null;

  const audioId = data.audio_id || data.source_audio?.audio_id || data.memory_id;
  const audioSource = data.audio_source || data.source_audio?.audio_source;
  const startTime = Math.max(0, parseFloat(data.start_time ?? data.source_audio?.start_time ?? 0) || 0);
  const endTime = Math.max(0, parseFloat(data.end_time ?? data.source_audio?.end_time ?? 0) || 0);
  const quote = data.verbatim_quote || data.source_audio?.verbatim_quote;

  const formatSec = (s) => `${Math.floor(s / 60)}:${Math.floor(s % 60).toString().padStart(2, '0')}`;

  return (
    <div className="space-y-6">
      {/* SECTION HEADER: Title & Era */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 bg-slate-900/70 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-md shadow-amber-500/10">
            <ArrowRightLeft className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase tracking-widest text-amber-400 font-bold block">
              Historical Bridge &bull; Then vs Now
            </span>
            <h3 className="text-2xl font-bold font-serif text-white tracking-tight">{data.topic}</h3>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs bg-slate-800/90 px-3.5 py-1.5 rounded-full text-slate-300 border border-slate-700 font-medium">
            Era: <strong className="text-amber-300 font-normal">{data.era_described}</strong>
          </span>
        </div>
      </div>

      {/* 2-COLUMN SECTION: (1) GRANDPA'S EXPERIENCE (THEN) vs (2) MODERN CONTEXT (NOW) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* PANEL 1: Grandpa's Experience (THEN) */}
        <div className="glass-panel rounded-2xl p-6 border border-amber-500/30 bg-gradient-to-b from-amber-950/20 via-slate-900/90 to-slate-950 flex flex-col justify-between shadow-xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/5 rounded-full blur-2xl pointer-events-none" />
          <div>
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-amber-900/40">
              <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-amber-400">
                <History className="w-4 h-4" />
                <span>Grandpa's Experience (THEN)</span>
              </div>
              <span className="text-[10px] font-mono text-amber-300/80 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                Authentic Voice
              </span>
            </div>
            <p className="text-sm text-amber-100/90 leading-relaxed font-serif whitespace-pre-wrap">
              {data.then_experience}
            </p>
          </div>
          {quote && (
            <div className="mt-4 pt-3 border-t border-amber-900/30">
              <p className="text-xs italic text-amber-300/80">
                "{quote}"
              </p>
            </div>
          )}
        </div>

        {/* PANEL 2: Modern Context (NOW) */}
        <div className="glass-panel rounded-2xl p-6 border border-sky-500/30 bg-gradient-to-b from-sky-950/20 via-slate-900/90 to-slate-950 flex flex-col justify-between shadow-xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-sky-500/5 rounded-full blur-2xl pointer-events-none" />
          <div>
            <div className="flex items-center justify-between pb-3 mb-4 border-b border-sky-900/40">
              <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-sky-400">
                <Sparkles className="w-4 h-4" />
                <span>Modern Context (NOW)</span>
              </div>
              <span className="text-[10px] font-mono text-sky-300/80 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/20">
                2020s Reality
              </span>
            </div>
            <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
              {data.now_reality}
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-sky-900/30 text-[11px] text-slate-400">
            Speed, convenience, and instant connectivity redefine daily life today.
          </div>
        </div>
      </div>

      {/* PANEL 3: COMPARISON & GENERATIONAL BRIDGE */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 bg-slate-900/80 space-y-4 shadow-xl">
        <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-amber-300">
          <MessageSquareHeart className="w-4 h-4 text-amber-400" />
          <span>Generational Comparison & Enduring Value</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
          {/* Enduring Value */}
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 space-y-1.5">
            <h4 className="text-[11px] font-mono uppercase tracking-wider text-amber-400 font-bold">
              The Enduring Principle
            </h4>
            <p className="text-xs text-amber-100/90 italic font-serif leading-relaxed">
              "{data.enduring_value || 'Patience, thoughtful communication, and deep human bonds remain timeless.'}"
            </p>
          </div>

          {/* Family Discussion Prompt */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1.5">
            <div className="flex items-center space-x-1.5 text-[11px] font-mono uppercase tracking-wider text-slate-400 font-bold">
              <HelpCircle className="w-3.5 h-3.5" />
              <span>Family Discussion Question</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              {data.reflection_question || 'What parts of grandfather’s era do we miss in our fast-paced digital world today?'}
            </p>
          </div>
        </div>
      </div>

      {/* PANEL 4: SOURCE RECORDING PLAYER */}
      <div className="glass-panel rounded-2xl p-5 border border-amber-900/40 bg-gradient-to-r from-amber-950/30 via-slate-950 to-slate-900/90 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 rounded-xl bg-amber-500/15 text-amber-400 border border-amber-500/30 flex-shrink-0">
            <Mic className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono uppercase tracking-widest text-amber-400 font-bold">
                Source Recording
              </span>
              {endTime > startTime ? (
                <span className="text-[10px] font-mono bg-slate-800 px-2 py-0.5 rounded text-amber-300 border border-slate-700">
                  {formatSec(startTime)} - {formatSec(endTime)}
                </span>
              ) : startTime > 0 ? (
                <span className="text-[10px] font-mono bg-slate-800 px-2 py-0.5 rounded text-amber-300 border border-slate-700">
                  Starts at {formatSec(startTime)}
                </span>
              ) : (
                <span className="text-[10px] font-mono bg-slate-800 px-2 py-0.5 rounded text-amber-300 border border-slate-700">
                  Full Story
                </span>
              )}
            </div>
            <p className="text-xs font-semibold text-white mt-0.5">
              {data.memory_title || data.source_audio?.title || data.topic}
            </p>
            {audioSource && (
              <p className="text-[10px] text-slate-400 font-mono">
                Preserved File: {audioSource}
              </p>
            )}
          </div>
        </div>

        <button
          onClick={handlePlaySource}
          className="inline-flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold text-xs transition shadow-lg shadow-amber-500/20 flex-shrink-0 cursor-pointer"
        >
          <Play className="w-4 h-4 fill-current" />
          <span>Play Original Recording</span>
        </button>
      </div>
    </div>
  );
}
