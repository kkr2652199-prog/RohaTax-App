import React from 'react';
import { Play, Pause, FastForward, Rewind, Square } from 'lucide-react';

interface ControlsProps {
  isPlaying: boolean;
  onPlayPause: () => void;
  onForward: () => void;
  onRewind: () => void;
  onStop: () => void;
}

const Controls: React.FC<ControlsProps> = ({ 
  isPlaying, 
  onPlayPause, 
  onForward, 
  onRewind,
  onStop
}) => {
  return (
    <div className="absolute bottom-10 left-1/2 -translate-x-1/2 pointer-events-auto">
      <div className="flex items-center gap-6 px-8 py-4 bg-black/40 backdrop-blur-xl border border-white/10 rounded-full shadow-2xl transition-all hover:bg-black/50 hover:scale-105 hover:border-white/20">
        
        {/* Rewind */}
        <button 
          onClick={onRewind}
          className="group relative flex items-center justify-center w-10 h-10 rounded-full text-white/70 hover:text-white hover:bg-white/10 transition-all active:scale-95"
          aria-label="Rewind 5s"
        >
          <Rewind size={20} className="fill-current" />
        </button>

        {/* Play/Pause (Main Action) */}
        <button 
          onClick={onPlayPause}
          className="group relative flex items-center justify-center w-16 h-16 rounded-full bg-white text-black shadow-lg shadow-white/10 hover:scale-110 active:scale-95 transition-all"
          aria-label={isPlaying ? "Pause" : "Play"}
        >
          {isPlaying ? (
            <Pause size={28} className="fill-current" />
          ) : (
            <Play size={28} className="fill-current ml-1" />
          )}
          {/* Glow effect */}
          <div className="absolute inset-0 rounded-full bg-white opacity-0 group-hover:opacity-30 blur-lg transition-opacity" />
        </button>

        {/* Stop */}
         <button 
          onClick={onStop}
          className="group relative flex items-center justify-center w-10 h-10 rounded-full text-white/70 hover:text-red-400 hover:bg-white/10 transition-all active:scale-95"
          aria-label="Stop"
        >
          <Square size={18} className="fill-current" />
        </button>

        {/* Forward */}
        <button 
          onClick={onForward}
          className="group relative flex items-center justify-center w-10 h-10 rounded-full text-white/70 hover:text-white hover:bg-white/10 transition-all active:scale-95"
          aria-label="Forward 5s"
        >
          <FastForward size={20} className="fill-current" />
        </button>

      </div>
      
      <div className="text-center mt-3">
        <p className="text-xs text-white/30 font-medium tracking-widest uppercase">
          Soundbar System Active
        </p>
      </div>
    </div>
  );
};

export default Controls;