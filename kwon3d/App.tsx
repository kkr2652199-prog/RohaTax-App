import React, { Suspense, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, ContactShadows } from '@react-three/drei';
import { GiftHandModel } from './components/GiftHandModel';
import { LucideGift, LucideSparkles } from 'lucide-react';

export default function App() {
  const [isOpen, setIsOpen] = useState(false);

  const toggleOpen = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div className="relative w-full h-screen overflow-hidden text-white font-sans select-none">
      
      {/* --- UI Header --- */}
      <div className="absolute top-0 left-0 w-full p-8 z-10 flex flex-col items-center pointer-events-none">
        <h1 className="text-5xl font-serif text-[#ffd700] drop-shadow-[0_4px_4px_rgba(0,0,0,0.8)] tracking-wide">
           Royal Gift
        </h1>
        <p className="text-white/60 text-sm mt-2 tracking-widest uppercase">
          Interactive 3D Experience
        </p>
      </div>

      {/* --- Bottom Controls --- */}
      <div className="absolute bottom-10 left-0 w-full z-10 flex justify-center pointer-events-auto">
        <button
          onClick={toggleOpen}
          className={`
            group relative flex items-center gap-3 px-10 py-4 rounded-full 
            transition-all duration-300 ease-out transform hover:scale-105 active:scale-95
            ${isOpen 
              ? 'bg-gradient-to-r from-gray-800 to-gray-900 border-gray-600' 
              : 'bg-gradient-to-r from-[#ffd700] to-[#b45309] border-[#ffd700]'
            }
            border-2 shadow-2xl
          `}
        >
          {isOpen ? (
             <>
               <span className="text-gray-400 font-bold text-lg tracking-wider">CLOSE GIFT</span>
             </>
          ) : (
            <>
               <LucideGift className="text-white fill-white/20 animate-pulse" size={24} />
               <span className="text-white font-bold text-lg tracking-wider text-shadow-sm">OPEN GIFT</span>
               <LucideSparkles className="text-white absolute -top-1 -right-2 animate-bounce" size={20} />
            </>
          )}
        </button>
      </div>

      {/* --- 3D Scene --- */}
      <Canvas
        shadows
        camera={{ position: [4, 3, 6], fov: 40 }}
        className="w-full h-full"
        dpr={[1, 2]}
      >
        {/* Warm, Moody Atmosphere */}
        <color attach="background" args={['transparent']} /> {/* Handled by CSS */}

        {/* Lighting */}
        <ambientLight intensity={0.4} color="#ffddaa" />
        
        {/* Main Spotlight creating dramatic shadows */}
        <spotLight 
          position={[5, 8, 5]} 
          angle={0.4} 
          penumbra={0.5} 
          intensity={2} 
          castShadow 
          shadow-mapSize={[1024, 1024]}
          shadow-bias={-0.0001}
          color="#fff5cc"
        />

        {/* Fill light for the dark side */}
        <pointLight position={[-5, 2, -5]} intensity={0.5} color="#bd5e5e" />

        {/* Rim light to highlight edges */}
        <spotLight position={[0, 5, -8]} intensity={3} color="#ffd700" distance={15} />

        {/* Environment for shiny reflections */}
        <Environment preset="lobby" />

        <Suspense fallback={null}>
          <group position={[0, -1, 0]}>
            
            {/* The Gift Model */}
            <GiftHandModel isOpen={isOpen} />

            {/* The "Table" */}
            <mesh position={[0, -0.1, 0]} receiveShadow>
              <cylinderGeometry args={[4, 4, 0.2, 64]} />
              <meshStandardMaterial 
                color="#222" 
                roughness={0.1} 
                metalness={0.2}
                envMapIntensity={1}
              />
            </mesh>

            {/* Shadows on the table */}
            <ContactShadows 
              position={[0, 0.01, 0]} 
              opacity={0.7} 
              scale={10} 
              blur={2} 
              far={2} 
              color="#000"
            />
          </group>
        </Suspense>

        <OrbitControls 
          enablePan={false} 
          enableZoom={true} 
          minPolarAngle={0} 
          maxPolarAngle={Math.PI / 2.2} // Prevent going below the table
          autoRotate={false} // Disabled as requested
          target={[0, 0.5, 0]}
        />
      </Canvas>
    </div>
  );
}