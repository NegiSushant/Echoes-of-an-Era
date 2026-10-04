import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Sparkles, Loader2, Search, Send } from 'lucide-react';
import ThenNow from '../components/ThenNow';
import { api } from '../services/api';

export default function Compare({ onPlayAudio }) {
  const [searchParams] = useSearchParams();
  const memoryIdFromUrl = searchParams.get('memoryId');

  const [memories, setMemories] = useState([]);
  const [selectedMemoryId, setSelectedMemoryId] = useState(memoryIdFromUrl ? parseInt(memoryIdFromUrl) : null);
  const [activeQuery, setActiveQuery] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const memList = await api.getMemories(0, 50);
        setMemories(memList);

        if (!selectedMemoryId && memList.length > 0) {
          setSelectedMemoryId(memList[0].id);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSelectedMemoryId(null);
    setActiveQuery(searchQuery.trim());
  };

  const handleSelectMemory = (id) => {
    setActiveQuery(null);
    setSelectedMemoryId(id);
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div>
        <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 text-xs font-medium mb-2 border border-amber-500/20">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Signature Time Capsule Feature</span>
        </div>
        <h1 className="text-3xl font-bold font-serif text-white">Then vs Now</h1>
        <p className="text-sm text-slate-400 mt-1 max-w-2xl">
          Compare the authentic lived reality of grandfather's era with contemporary 2020s life, bridging generations through enduring values and family discussion prompts.
        </p>
      </div>

      {isLoading ? (
        <div className="glass-panel p-16 text-center rounded-2xl border border-slate-800">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-amber-500 mb-3" />
          <p className="text-sm text-slate-400">Loading historical reflections...</p>
        </div>
      ) : memories.length === 0 ? (
        <div className="glass-panel p-12 text-center rounded-2xl border border-slate-800">
          <p className="text-slate-300 font-medium">No voice memories deposited yet.</p>
          <p className="text-slate-500 text-xs mt-1">Upload a recording on the Home page to generate Then vs Now comparisons.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Controls: Search Topic or Pick Memory */}
          <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
            {/* Quick Memory Selector */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 mr-1">
                Select Memory:
              </span>
              {memories.map((mem) => (
                <button
                  key={mem.id}
                  onClick={() => handleSelectMemory(mem.id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-medium transition cursor-pointer ${selectedMemoryId === mem.id && !activeQuery
                      ? 'bg-amber-500 text-slate-950 font-bold shadow-lg shadow-amber-500/20'
                      : 'bg-slate-900 text-slate-300 hover:text-white border border-slate-800'
                    }`}
                >
                  {mem.title}
                </button>
              ))}
            </div>

            {/* Topic Comparison Search Bar */}
            <form onSubmit={handleSearchSubmit} className="flex items-center space-x-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="text"
                  placeholder="Compare a topic (e.g. Letters)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-slate-950 border border-slate-800 text-xs rounded-xl pl-8 pr-3 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition w-56 sm:w-64"
                />
              </div>
              <button
                type="submit"
                disabled={!searchQuery.trim()}
                className="px-3 py-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 text-xs font-bold rounded-xl transition"
              >
                Compare
              </button>
            </form>
          </div>

          {/* Active Then vs Now Card */}
          {activeQuery ? (
            <ThenNow
              key={`query-${activeQuery}`}
              query={activeQuery}
              onPlayAudio={onPlayAudio}
            />
          ) : selectedMemoryId ? (
            <ThenNow
              key={`mem-${selectedMemoryId}`}
              memoryId={selectedMemoryId}
              onPlayAudio={onPlayAudio}
            />
          ) : null}
        </div>
      )}
    </div>
  );
}
