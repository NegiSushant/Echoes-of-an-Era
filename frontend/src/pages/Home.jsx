import React, { useState, useEffect } from 'react';
import { Mic, Sparkles, BookOpen, Clock, ShieldCheck, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import AudioUploader from '../components/AudioUploader';
import MemoryCard from '../components/MemoryCard';
import { api } from '../services/api';

export default function Home({ onPlayAudio }) {
  const [recentMemories, setRecentMemories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchMemories = async () => {
    try {
      const data = await api.getAudioRecords(0, 6);
      setRecentMemories(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, []);

  const [processingId, setProcessingId] = useState(null);
  const [isBatchProcessing, setIsBatchProcessing] = useState(false);

  const handleProcessRecording = async (memoryId) => {
    setProcessingId(memoryId);
    try {
      await api.processMemoryPipeline(memoryId);
      await fetchMemories();
    } catch (err) {
      alert(`Processing failed: ${err.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  const handleProcessAll = async () => {
    setIsBatchProcessing(true);
    try {
      await api.processAllPendingMemories();
      await fetchMemories();
    } catch (err) {
      alert(`Batch processing failed: ${err.message}`);
    } finally {
      setIsBatchProcessing(false);
    }
  };

  const pendingCount = recentMemories.filter((m) => m.status === 'uploaded').length;

  return (
    <div className="space-y-12 pb-16">
      {/* Hero Section */}
      <div className="relative text-center py-12 px-4 rounded-3xl overflow-hidden glass-panel border border-amber-900/30">
        <div className="absolute inset-0 bg-gradient-to-b from-amber-500/10 via-transparent to-transparent pointer-events-none" />
        
        <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-medium mb-6">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Hacktoberfest Weekend Challenge 2026: Build for a Friend</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold font-serif tracking-tight text-white mb-4">
          Echoes of an <span className="gold-gradient-text">Era</span>
        </h1>

        <p className="text-lg sm:text-xl text-slate-300 font-serif italic max-w-2xl mx-auto mb-6">
          "A living AI time capsule built from my grandfather's voice."
        </p>

        {/* Immutable Core Principle */}
        <div className="max-w-xl mx-auto p-3.5 rounded-2xl bg-amber-950/40 border border-amber-700/30 text-xs text-amber-200/90 flex items-center justify-center space-x-2 shadow-inner">
          <ShieldCheck className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <span>
            <strong>Core Principle:</strong> AI interprets the memories. It does not create the memories.
          </span>
        </div>

        {/* Navigation Quick Links */}
        <div className="mt-8 flex flex-wrap justify-center gap-4">
          <Link
            to="/timeline"
            className="px-6 py-3 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-medium text-sm transition shadow-lg shadow-amber-900/40 flex items-center space-x-2"
          >
            <span>Explore Life Timeline</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/ask"
            className="px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-sm transition border border-slate-700 flex items-center space-x-2"
          >
            <span>Ask Grandfather</span>
          </Link>
          <Link
            to="/compare"
            className="px-6 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-300 font-medium text-sm transition border border-amber-500/30 flex items-center space-x-2"
          >
            <span>Then vs Now</span>
          </Link>
        </div>
      </div>

      {/* Grid: Audio Deposit & Quick Archive */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        <div className="lg:col-span-1">
          <AudioUploader onUploadSuccess={fetchMemories} onPlayAudio={onPlayAudio} />
        </div>

        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <BookOpen className="w-5 h-5 text-amber-500" />
              <h2 className="text-xl font-bold font-serif text-white">Preserved Recordings</h2>
            </div>
            <div className="flex items-center space-x-3">
              {pendingCount > 0 && (
                <button
                  onClick={handleProcessAll}
                  disabled={isBatchProcessing}
                  className="px-3 py-1 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold transition flex items-center space-x-1.5 shadow disabled:opacity-50"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{isBatchProcessing ? 'Processing All...' : `Process All Pending (${pendingCount})`}</span>
                </button>
              )}
              <span className="text-xs text-slate-400">
                {recentMemories.length} audio {recentMemories.length === 1 ? 'file' : 'files'} vaulted
              </span>
            </div>
          </div>

          {isLoading ? (
            <div className="glass-panel p-8 text-center rounded-2xl text-slate-400 text-sm">
              Loading preserved memories...
            </div>
          ) : recentMemories.length === 0 ? (
            <div className="glass-panel p-10 text-center rounded-2xl border border-slate-800">
              <Clock className="w-10 h-10 mx-auto text-amber-500/40 mb-3" />
              <p className="text-slate-300 text-sm font-medium">No voice recordings deposited yet.</p>
              <p className="text-slate-500 text-xs mt-1">Upload a recording on the left to safely store grandfather's original voice.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {recentMemories.map((rec) => (
                <div key={rec.memory_id} className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between">
                  <div className="flex items-center space-x-3 truncate mr-3">
                    <div className="w-10 h-10 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center flex-shrink-0 border border-amber-500/20">
                      <Mic className="w-5 h-5" />
                    </div>
                    <div className="truncate">
                      <h4 className="text-sm font-medium text-white truncate">{rec.file_name}</h4>
                      <div className="flex items-center space-x-2 text-[11px] text-slate-400 mt-0.5">
                        <span className="text-amber-400 font-mono">{(rec.duration || 0).toFixed(1)}s</span>
                        <span>&bull;</span>
                        <span>{((rec.file_size_bytes || 0) / (1024 * 1024)).toFixed(2)} MB</span>
                        <span>&bull;</span>
                        <span
                          className={`px-1.5 py-0.2 rounded text-[10px] uppercase font-mono ${
                            rec.status === 'completed'
                              ? 'bg-emerald-500/10 text-emerald-400'
                              : 'bg-amber-500/10 text-amber-400'
                          }`}
                        >
                          {rec.status}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 flex-shrink-0">
                    {rec.status === 'uploaded' && (
                      <button
                        onClick={() => handleProcessRecording(rec.memory_id)}
                        disabled={processingId === rec.memory_id}
                        className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 text-white text-xs font-semibold transition disabled:opacity-50"
                      >
                        <Sparkles className="w-3 h-3" />
                        <span>{processingId === rec.memory_id ? 'Transcribing...' : 'Process Memory'}</span>
                      </button>
                    )}
                    <button
                      onClick={() =>
                        onPlayAudio &&
                        onPlayAudio({
                          audioId: rec.memory_id,
                          startTime: 0,
                          title: rec.file_name
                        })
                      }
                      className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 text-xs font-semibold border border-amber-500/30 transition flex-shrink-0"
                    >
                      <span>Play Audio</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
