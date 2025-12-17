import React, { useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { ChandelierScene } from './components/ChandelierScene';
import { LightingState } from './types';
import { Sun, Moon, Palette } from 'lucide-react';

const App: React.FC = () => {
  const [lightState, setLightState] = useState<LightingState>({
    intensity: 1.5,
    warmth: 0.8,
    lightColor: '#ffaa44',
  });

  const handleIntensityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLightState(prev => ({ ...prev, intensity: parseFloat(e.target.value) }));
  };

  const handleColorChange = (color: string) => {
    setLightState(prev => ({ ...prev, lightColor: color }));
  };

  return (
    <div className="relative w-full h-screen bg-neutral-900 text-white overflow-hidden">
      
      {/* 3D Canvas */}
      <div className="absolute inset-0 z-0">
        <Canvas shadows dpr={[1, 2]} camera={{ position: [8, 5, 12], fov: 45 }}>
          <color attach="background" args={['#101010']} />
          <ChandelierScene lightState={lightState} />
        </Canvas>
      </div>

      {/* Header / Title */}
      <div className="absolute top-0 left-0 p-8 z-10 pointer-events-none">
        <h1 className="text-5xl font-thin tracking-wider text-amber-50 font-serif drop-shadow-md">
          Lumière Élégante
        </h1>
        <p className="text-amber-200/60 mt-2 text-lg font-light tracking-wide">
          Interactive 3D Visualization
        </p>
      </div>

      {/* Controls Panel */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 w-11/12 max-w-2xl bg-black/40 backdrop-blur-md border border-white/10 rounded-2xl p-6 z-10 shadow-2xl transition-all duration-300 hover:bg-black/50">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          
          {/* Intensity Slider */}
          <div className="flex flex-col w-full md:w-1/2 gap-2">
            <div className="flex items-center gap-2 text-amber-100/80 text-sm font-medium uppercase tracking-widest">
              <Sun size={16} /> Brightness
            </div>
            <input
              type="range"
              min="0"
              max="5"
              step="0.1"
              value={lightState.intensity}
              onChange={handleIntensityChange}
              className="w-full h-1 bg-white/20 rounded-lg appearance-none cursor-pointer accent-amber-400 hover:accent-amber-300 transition-colors"
            />
            <div className="flex justify-between text-xs text-white/30 px-1">
              <span>Off</span>
              <span>Max</span>
            </div>
          </div>

          {/* Color Toggles */}
          <div className="flex flex-col w-full md:w-auto gap-3 items-center md:items-start">
             <div className="flex items-center gap-2 text-amber-100/80 text-sm font-medium uppercase tracking-widest">
              <Palette size={16} /> Atmosphere
            </div>
            <div className="flex gap-3">
              <button 
                onClick={() => handleColorChange('#ffaa44')}
                className={`w-10 h-10 rounded-full border-2 transition-all duration-300 shadow-lg ${lightState.lightColor === '#ffaa44' ? 'border-white scale-110 shadow-amber-500/40' : 'border-transparent opacity-70 hover:opacity-100'}`}
                style={{ backgroundColor: '#ffaa44' }}
                title="Warm Gold"
              />
              <button 
                onClick={() => handleColorChange('#ffebcd')}
                className={`w-10 h-10 rounded-full border-2 transition-all duration-300 shadow-lg ${lightState.lightColor === '#ffebcd' ? 'border-white scale-110 shadow-white/40' : 'border-transparent opacity-70 hover:opacity-100'}`}
                style={{ backgroundColor: '#ffebcd' }}
                title="Neutral Cream"
              />
              <button 
                onClick={() => handleColorChange('#e0f7fa')}
                className={`w-10 h-10 rounded-full border-2 transition-all duration-300 shadow-lg ${lightState.lightColor === '#e0f7fa' ? 'border-white scale-110 shadow-cyan-400/40' : 'border-transparent opacity-70 hover:opacity-100'}`}
                style={{ backgroundColor: '#e0f7fa' }}
                title="Cool Daylight"
              />
            </div>
          </div>

        </div>
      </div>

      {/* Credits / Info */}
      <div className="absolute top-8 right-8 text-right z-10 hidden md:block pointer-events-none">
        <div className="text-white/40 text-xs tracking-widest font-mono">
          MODEL: CLASSIC-8-ARM<br/>
          MATERIAL: AGED BRASS & FABRIC<br/>
          ACCENT: AMBER CRYSTAL
        </div>
      </div>
      
    </div>
  );
};

export default App;