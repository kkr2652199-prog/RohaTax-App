import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, ContactShadows, Stars, Loader } from '@react-three/drei';
import { ImperialCrown } from './components/ImperialCrown';

const App: React.FC = () => {
  return (
    <>
      <div className="w-full h-screen bg-neutral-950 relative">
        <Canvas
          shadows
          camera={{ position: [0, 2, 8], fov: 35 }}
          gl={{ preserveDrawingBuffer: true, antialias: true }}
          dpr={[1, 2]} // Handle high DPI screens
        >
          <Suspense fallback={null}>
            {/* Lighting Environment for Gold Reflections */}
            <Environment preset="lobby" />
            
            <ambientLight intensity={0.2} />
            <spotLight 
              position={[10, 10, 10]} 
              angle={0.15} 
              penumbra={1} 
              intensity={2} 
              castShadow 
              shadow-mapSize={[2048, 2048]} 
            />
            <pointLight position={[-10, -10, -10]} intensity={0.5} color="#blue" />

            {/* The Main 3D Model */}
            <group position={[0, -1, 0]}>
              <ImperialCrown />
            </group>

            {/* Floor Shadows */}
            <ContactShadows 
              resolution={1024} 
              scale={20} 
              blur={2} 
              opacity={0.5} 
              far={10} 
              color="#000000" 
            />

            {/* User Interaction */}
            <OrbitControls 
              minPolarAngle={0} 
              maxPolarAngle={Math.PI / 2} 
              enablePan={false}
              minDistance={4}
              maxDistance={15}
              autoRotate={true}
              autoRotateSpeed={0.5}
            />
            
            <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
          </Suspense>
        </Canvas>

        {/* Minimal UI Overlay */}
        <div className="absolute top-8 left-0 w-full text-center pointer-events-none">
          <h1 className="text-3xl md:text-5xl font-serif italic text-amber-200 tracking-widest drop-shadow-lg opacity-80">
            Imperial Crown
          </h1>
          <p className="text-xs text-amber-500/50 mt-2 uppercase tracking-[0.3em]">Procedural 3D Reconstruction</p>
        </div>
      </div>
      <Loader />
    </>
  );
};

export default App;