import React from 'react';
import { Scene } from './components/Scene';
import { DesignAdvisor } from './components/DesignAdvisor';

function App() {
  return (
    <div className="relative w-full h-screen bg-black overflow-hidden">
      
      {/* 3D Scene Background */}
      <div className="absolute inset-0 z-0">
        <Scene />
      </div>

      {/* Minimal Overlay UI */}
      <div className="absolute top-0 left-0 w-full p-8 z-10 pointer-events-none">
        <header className="flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-serif text-gold-100 tracking-wider drop-shadow-lg">
              MAISON <span className="text-gold-500">D'OR</span>
            </h1>
          </div>
        </header>
      </div>

      <DesignAdvisor />
    </div>
  );
}

export default App;