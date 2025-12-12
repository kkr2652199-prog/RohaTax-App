import React, { useState, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { Loader } from '@react-three/drei';
import Scene from './components/Scene';

export default function App() {
  const [isPlaying, setIsPlaying] = useState(false);

  // Simple state toggles for 3D UI
  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleStop = () => {
    setIsPlaying(false);
  };

  const handleForward = () => {
    console.log("Forward");
  };

  const handleRewind = () => {
    console.log("Rewind");
  };

  return (
    <div className="relative w-full h-full bg-[#050505]">
      {/* 3D Canvas */}
      <Canvas shadows camera={{ position: [0, 0, 5], fov: 45 }}>
        <Suspense fallback={null}>
          <Scene 
            isPlaying={isPlaying} 
            onPlayPause={handlePlayPause}
            onForward={handleForward}
            onRewind={handleRewind}
            onStop={handleStop}
          />
        </Suspense>
      </Canvas>
      <Loader />

      {/* Minimal Title Overlay */}
      <div className="absolute top-0 left-0 w-full p-6 pointer-events-none">
        <h1 className="text-white/40 font-light tracking-[0.3em] text-xs uppercase border-l-2 border-yellow-600 pl-4">
          Signature Series <br/>
          <span className="font-serif text-2xl text-white/90">Midnight Luxury</span>
        </h1>
      </div>
    </div>
  );
}