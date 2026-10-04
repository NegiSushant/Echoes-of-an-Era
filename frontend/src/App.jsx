import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Mic, BookOpen, MessageSquare, ArrowRightLeft, Radio, Heart } from 'lucide-react';
import Home from './pages/Home';
import Timeline from './pages/Timeline';
import Memories from './pages/Memories';
import Ask from './pages/Ask';
import Compare from './pages/Compare';
import AudioPlayer from './components/AudioPlayer';
import { api } from './services/api';

function Navigation() {
  const location = useLocation();

  const navItems = [
    { label: 'Home', path: '/', icon: Mic },
    { label: 'Timeline', path: '/timeline', icon: BookOpen },
    { label: 'Ask Grandfather', path: '/ask', icon: MessageSquare },
    { label: 'Then vs Now', path: '/compare', icon: ArrowRightLeft },
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 mb-8 px-4 sm:px-8 py-3.5">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        {/* Brand */}
        <Link to="/" className="flex items-center space-x-3 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center text-white shadow-lg shadow-amber-500/20 group-hover:scale-105 transition">
            <Radio className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold font-serif tracking-tight text-white group-hover:text-amber-300 transition">
              Echoes of an Era
            </h1>
            <p className="text-[10px] text-amber-400 font-mono tracking-wider uppercase">
              Grandfather's Voice Capsule
            </p>
          </div>
        </Link>

        {/* Links */}
        <nav className="flex items-center space-x-1 sm:space-x-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-medium transition ${
                  isActive
                    ? 'bg-amber-500/10 text-amber-300 border border-amber-500/30 font-semibold'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/50'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}

export default function App() {
  const [activeAudio, setActiveAudio] = useState(null);

  const handlePlayAudio = ({ audioId, startTime = 0, title }) => {
    setActiveAudio({ audioId, startTime, title, timestamp: Date.now() });
  };

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#0b0d11] text-slate-100 flex flex-col font-sans selection:bg-amber-600 selection:text-white">
        <Navigation />

        <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-8">
          <Routes>
            <Route path="/" element={<Home onPlayAudio={handlePlayAudio} />} />
            <Route path="/timeline" element={<Timeline onPlayAudio={handlePlayAudio} />} />
            <Route path="/memories" element={<Timeline onPlayAudio={handlePlayAudio} />} />
            <Route path="/ask" element={<Ask onPlayAudio={handlePlayAudio} />} />
            <Route path="/compare" element={<Compare onPlayAudio={handlePlayAudio} />} />
          </Routes>
        </main>

        {/* Docked Authentic Audio Player */}
        {activeAudio && (
          <div className="fixed bottom-4 left-4 right-4 max-w-2xl mx-auto z-50">
            <AudioPlayer
              key={`${activeAudio.audioId}-${activeAudio.timestamp}`}
              audioId={activeAudio.audioId}
              initialTime={activeAudio.startTime}
              autoPlay={true}
              title={activeAudio.title}
            />
          </div>
        )}

        {/* Footer */}
        <footer className="border-t border-slate-900 py-6 mt-16 text-center text-xs text-slate-500">
          <p>
            Built with reverence for the Hacktoberfest Weekend Challenge 2026: <em>"Build for a Friend"</em>.
          </p>
          <p className="text-[11px] text-slate-600 mt-1">
            "AI interprets the memories. It does not create the memories." &bull; Grandfather's Voice Archive
          </p>
        </footer>
      </div>
    </BrowserRouter>
  );
}
