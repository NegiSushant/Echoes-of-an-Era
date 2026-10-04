import { useState, useEffect } from 'react';
import { Clock, Calendar, Sparkles, Filter, Search, RotateCcw, AlertCircle, Loader2, BookOpen, Volume2 } from 'lucide-react';
import MemoryCard from '../components/MemoryCard';
import { api } from '../services/api';

export default function Timeline({ onPlayAudio }) {
  const [timelineData, setTimelineData] = useState(null);
  const [selectedEra, setSelectedEra] = useState('All');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadTimeline();
  }, []);

  const loadTimeline = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getTimeline();
      setTimelineData(data);
    } catch (err) {
      console.error('Failed to load timeline:', err);
      setError('Could not load life timeline. Please verify the backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetFilters = () => {
    setSelectedEra('All');
    setSelectedCategory('All');
    setSearchQuery('');
  };

  // Filter memories according to selected era, category, and search text
  const getFilteredEras = () => {
    if (!timelineData || !timelineData.eras) return [];

    return timelineData.eras
      .filter((eraGroup) => selectedEra === 'All' || eraGroup.era === selectedEra)
      .map((eraGroup) => {
        const filteredMemories = eraGroup.memories.filter((mem) => {
          // Category match
          const matchesCategory =
            selectedCategory === 'All' ||
            (mem.tags && mem.tags.some((t) => t.toLowerCase() === selectedCategory.toLowerCase())) ||
            (mem.title && mem.title.toLowerCase().includes(selectedCategory.toLowerCase()));

          // Search query match
          const q = searchQuery.trim().toLowerCase();
          const matchesSearch =
            !q ||
            (mem.title && mem.title.toLowerCase().includes(q)) ||
            (mem.summary && mem.summary.toLowerCase().includes(q)) ||
            (mem.location && mem.location.toLowerCase().includes(q)) ||
            (mem.tags && mem.tags.some((t) => t.toLowerCase().includes(q)));

          return matchesCategory && matchesSearch;
        });

        return {
          ...eraGroup,
          filteredMemories
        };
      })
      .filter((eraGroup) => eraGroup.filteredMemories.length > 0);
  };

  const filteredEras = getFilteredEras();
  const totalFilteredMemories = filteredEras.reduce((acc, e) => acc + e.filteredMemories.length, 0);

  return (
    <div className="space-y-8 pb-20">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 text-xs font-medium mb-2 border border-amber-500/20">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Chronological & Thematic Journey</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold font-serif text-white tracking-tight">
            Grandfather's Life Timeline
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-xl">
            Step through his eras, cultural traditions, and life lessons, automatically organized from his recorded words.
          </p>
        </div>

        {/* Quick Stats */}
        {timelineData && (
          <div className="flex items-center space-x-3 text-xs bg-slate-900/80 border border-slate-800 px-4 py-2 rounded-2xl w-fit">
            <div>
              <span className="text-slate-400">Total Memories:</span>{' '}
              <strong className="text-amber-400 font-mono text-sm">{timelineData.total_memories}</strong>
            </div>
            <span className="text-slate-700">&bull;</span>
            <div>
              <span className="text-slate-400">Eras Vaulted:</span>{' '}
              <strong className="text-slate-200 font-mono text-sm">{timelineData.eras.length}</strong>
            </div>
          </div>
        )}
      </div>

      {/* Filter & Search Bar */}
      {timelineData && (
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search across eras, stories, and advice..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700/80 focus:border-amber-500 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none transition"
              />
            </div>

            {/* Reset Button */}
            {(selectedEra !== 'All' || selectedCategory !== 'All' || searchQuery) && (
              <button
                onClick={handleResetFilters}
                className="flex items-center justify-center space-x-1.5 px-3 py-2 text-xs text-amber-400 hover:text-amber-300 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 rounded-xl transition cursor-pointer flex-shrink-0"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reset Filters</span>
              </button>
            )}
          </div>

          {/* Era Filter Pills */}
          <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1 flex-shrink-0 mr-1">
              <Calendar className="w-3.5 h-3.5 text-amber-400" />
              <span>Era:</span>
            </span>
            <button
              onClick={() => setSelectedEra('All')}
              className={`px-3 py-1.5 rounded-xl font-medium transition flex-shrink-0 cursor-pointer ${selectedEra === 'All'
                ? 'bg-amber-500 text-slate-950 font-bold shadow-md shadow-amber-500/20'
                : 'bg-slate-900 text-slate-300 hover:text-white border border-slate-800'
                }`}
            >
              All Eras ({timelineData.total_memories})
            </button>
            {timelineData.eras.map((eraGroup) => (
              <button
                key={eraGroup.era}
                onClick={() => setSelectedEra(eraGroup.era)}
                className={`px-3 py-1.5 rounded-xl font-medium transition flex-shrink-0 cursor-pointer ${selectedEra === eraGroup.era
                  ? 'bg-amber-500 text-slate-950 font-bold shadow-md shadow-amber-500/20'
                  : 'bg-slate-900 text-slate-300 hover:text-white border border-slate-800'
                  }`}
              >
                {eraGroup.era} ({eraGroup.count})
              </button>
            ))}
          </div>

          {/* Category Filter Pills */}
          {timelineData.categories && timelineData.categories.length > 1 && (
            <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1 flex-shrink-0 mr-1">
                <Filter className="w-3.5 h-3.5 text-sky-400" />
                <span>Topic:</span>
              </span>
              {timelineData.categories.slice(0, 10).map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition flex-shrink-0 cursor-pointer ${selectedCategory === cat
                    ? 'bg-sky-500/20 text-sky-300 border border-sky-400/40 font-bold'
                    : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-slate-800/80'
                    }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Content Area */}
      {isLoading ? (
        <div className="glass-panel p-16 text-center rounded-2xl border border-slate-800 space-y-3">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-amber-500" />
          <h4 className="text-sm font-semibold text-slate-200">Building Life Timeline...</h4>
          <p className="text-xs text-slate-400">Extracting eras and themes from authentic voice recordings.</p>
        </div>
      ) : error ? (
        <div className="glass-panel p-8 text-center rounded-2xl border border-red-900/40 text-red-400 space-y-3">
          <AlertCircle className="w-8 h-8 mx-auto text-red-500" />
          <p className="text-sm font-medium">{error}</p>
          <button
            onClick={loadTimeline}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded-xl border border-slate-700"
          >
            Retry Loading Timeline
          </button>
        </div>
      ) : filteredEras.length === 0 ? (
        <div className="glass-panel p-16 text-center rounded-2xl border border-slate-800 space-y-3">
          <Clock className="w-12 h-12 mx-auto text-amber-500/40" />
          <h4 className="text-base font-semibold text-slate-300">No memories match your filter</h4>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {timelineData?.total_memories === 0
              ? "Deposit your grandfather's voice recording to begin charting his life timeline."
              : 'Try clearing your search query or selecting a different era or topic.'}
          </p>
          <button
            onClick={handleResetFilters}
            className="mt-2 inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-amber-500 text-slate-950 font-bold text-xs hover:bg-amber-400 transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Show All Memories</span>
          </button>
        </div>
      ) : (
        /* Vertical Chronological Timeline Tree */
        <div className="space-y-12">
          {filteredEras.map((eraGroup, eIdx) => (
            <div key={eraGroup.era} className="space-y-6">
              {/* Era Header Banner */}
              <div className="sticky top-20 z-10 py-2.5 px-4 rounded-xl glass-panel border border-amber-800/40 bg-slate-950/90 shadow-lg flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <div className="w-3 h-3 rounded-full bg-amber-500 animate-pulse shadow-md shadow-amber-500/50" />
                  <h3 className="text-base font-bold font-serif text-white tracking-wide">
                    Era: {eraGroup.era}
                  </h3>
                </div>
                <span className="text-xs font-mono text-amber-400 bg-amber-500/10 px-2.5 py-0.5 rounded-full border border-amber-500/20">
                  {eraGroup.filteredMemories.length} {eraGroup.filteredMemories.length === 1 ? 'memory' : 'memories'}
                </span>
              </div>

              {/* Connected Timeline Backbone */}
              <div className="relative pl-6 sm:pl-8 border-l-2 border-amber-600/30 space-y-8 ml-3 sm:ml-4">
                {eraGroup.filteredMemories.map((mem, mIdx) => (
                  <div key={mem.id || mIdx} className="relative group">
                    {/* Glowing Node on Timeline Axis */}
                    <div className="absolute -left-[31px] sm:-left-[39px] top-6 w-4 h-4 rounded-full bg-slate-950 border-2 border-amber-400 group-hover:scale-125 transition-transform shadow-lg shadow-amber-500/40" />

                    {/* Rich Memory Card */}
                    <MemoryCard memory={mem} onPlayAudio={onPlayAudio} />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
