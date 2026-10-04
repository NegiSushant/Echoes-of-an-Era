import { useState, useEffect } from 'react';
import { Search, LayoutGrid, GitCommit, Loader2 } from 'lucide-react';
import MemoryCard from '../components/MemoryCard';
import Timeline from '../components/Timeline';
import { api } from '../services/api';

export default function Memories({ onPlayAudio }) {
  const [memories, setMemories] = useState([]);
  const [viewMode, setViewMode] = useState('timeline'); // 'timeline' or 'grid'
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadMemories();
  }, []);

  const loadMemories = async () => {
    setIsLoading(true);
    try {
      const data = await api.getMemories(0, 100);
      setMemories(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      return loadMemories();
    }
    setIsSearching(true);
    try {
      const res = await api.searchMemories(searchQuery.trim(), 10);
      const mapped = res.results.map((r) => r.memory);
      setMemories(mapped);
    } catch (err) {
      console.error('Semantic search failed', err);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold font-serif text-white">Grandfather's Archive</h1>
          <p className="text-sm text-slate-400 mt-1">
            Chronological and thematic records of living memories
          </p>
        </div>

        {/* Search Bar & View Mode Toggle */}
        <div className="flex flex-wrap items-center gap-3">
          <form onSubmit={handleSearch} className="relative flex-1 sm:w-80">
            <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Semantic search (e.g. 'work ethic')..."
              className="w-full bg-slate-900 border border-slate-700 focus:border-amber-500 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none transition"
            />
          </form>

          {/* Toggle */}
          <div className="flex items-center bg-slate-900 border border-slate-800 p-1 rounded-xl">
            <button
              onClick={() => setViewMode('timeline')}
              className={`p-2 rounded-lg text-xs flex items-center space-x-1.5 transition ${viewMode === 'timeline'
                  ? 'bg-amber-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
                }`}
            >
              <GitCommit className="w-4 h-4" />
              <span className="hidden sm:inline">Timeline</span>
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-lg text-xs flex items-center space-x-1.5 transition ${viewMode === 'grid'
                  ? 'bg-amber-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
                }`}
            >
              <LayoutGrid className="w-4 h-4" />
              <span className="hidden sm:inline">Grid</span>
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {isLoading || isSearching ? (
        <div className="glass-panel p-16 text-center rounded-2xl">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-amber-500 mb-3" />
          <p className="text-sm text-slate-400">Searching grandfather's memory embeddings...</p>
        </div>
      ) : memories.length === 0 ? (
        <div className="glass-panel p-12 text-center rounded-2xl border border-slate-800">
          <p className="text-slate-300 font-medium">No matching memories found.</p>
          <button
            onClick={() => {
              setSearchQuery('');
              loadMemories();
            }}
            className="mt-3 text-xs text-amber-400 hover:underline"
          >
            Reset search
          </button>
        </div>
      ) : viewMode === 'timeline' ? (
        <Timeline memories={memories} onPlayAudio={onPlayAudio} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {memories.map((mem) => (
            <MemoryCard key={mem.id} memory={mem} onPlayAudio={onPlayAudio} />
          ))}
        </div>
      )}
    </div>
  );
}
