import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, ContactShadows, PresentationControls } from '@react-three/drei';
import { Showcase } from './Showcase';
import { JewelryBox } from './JewelryBox';

export const Scene: React.FC = () => {
  const showcaseWidth = 20;
  const showcaseHeight = 3;
  const showcaseDepth = 3;
  const boxCount = 5;

  // Calculate positions to distribute 5 boxes evenly along the top
  const innerWidth = showcaseWidth - 3; 
  const spacing = innerWidth / (boxCount - 1);
  
  const items = Array.from({ length: boxCount }).map((_, index) => {
    const x = -innerWidth / 2 + (index * spacing);
    
    // Position boxes ON TOP of the glass case.
    // Showcase is centered at y=0 relative to its group.
    // The top of the showcase glass is at y = +showcaseHeight/2 = 1.5.
    // The new JewelryBox height is 0.7.
    // We want the bottom of the JewelryBox at 1.5.
    // Center Y = 1.5 + (0.7 / 2) = 1.85.
    
    const boxY = (showcaseHeight / 2) + 0.35;

    return {
      id: index,
      boxPosition: [x, boxY, 0] as [number, number, number],
    };
  });

  return (
    <div className="w-full h-screen bg-neutral-900">
      <Canvas shadows camera={{ position: [0, 8, 18], fov: 35 }}>
        <fog attach="fog" args={['#050505', 10, 60]} />
        <Suspense fallback={null}>
          <PresentationControls 
            global 
            zoom={0.8} 
            rotation={[0, 0, 0]} 
            polar={[-Math.PI / 6, Math.PI / 6]} 
            azimuth={[-Math.PI / 6, Math.PI / 6]}
            snap={true}
          >
            {/* Move the whole group up slightly because legs are below */}
            <group position={[0, -0.5, 0]}>
                <Showcase width={showcaseWidth} height={showcaseHeight} depth={showcaseDepth} />
                
                {items.map((item) => (
                    <JewelryBox key={item.id} position={item.boxPosition} />
                ))}
            </group>
          </PresentationControls>

          {/* Lighting Environment */}
          <Environment preset="lobby" blur={0.8} background={false} />
          
          <ambientLight intensity={0.4} />
          <spotLight 
            position={[5, 20, 10]} 
            angle={0.3} 
            penumbra={0.5} 
            intensity={2} 
            castShadow 
            shadow-bias={-0.0001}
          />
          <spotLight 
            position={[-5, 20, 10]} 
            angle={0.3} 
            penumbra={0.5} 
            intensity={2} 
            castShadow 
            shadow-bias={-0.0001}
          />
          
          <ContactShadows resolution={1024} scale={60} blur={2} opacity={0.6} far={10} color="#000000" />
        </Suspense>

        <OrbitControls makeDefault minPolarAngle={0} maxPolarAngle={Math.PI / 2.2} />
      </Canvas>
    </div>
  );
};