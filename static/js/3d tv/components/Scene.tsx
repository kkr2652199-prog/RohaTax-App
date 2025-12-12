import React from 'react';
import { Environment, PresentationControls, ContactShadows, Float } from '@react-three/drei';
import TVModel from './TVModel';

interface SceneProps {
  isPlaying: boolean;
  onPlayPause: () => void;
  onForward: () => void;
  onRewind: () => void;
  onStop: () => void;
}

const Scene: React.FC<SceneProps> = ({ 
  isPlaying, 
  onPlayPause, 
  onForward, 
  onRewind, 
  onStop 
}) => {
  return (
    <>
      <color attach="background" args={['#050505']} />
      
      {/* Dramatic Luxury Lighting */}
      <ambientLight intensity={0.2} />
      
      {/* Key Light (Cool) */}
      <spotLight 
        position={[5, 5, 5]} 
        angle={0.25} 
        penumbra={1} 
        intensity={2} 
        castShadow 
        shadow-bias={-0.0001}
        color="#eef"
      />
      
      {/* Rim Light (Warm/Gold) - Highlights edges */}
      <spotLight 
        position={[-5, 2, -2]} 
        angle={0.5} 
        intensity={3} 
        color="#ffaa44" 
      />

      {/* Fill Light */}
      <pointLight position={[0, -2, 3]} intensity={0.5} color="#ccddff" />

      {/* High contrast reflections */}
      <Environment preset="city" />

      {/* Interactive Container - 360 Degree Rotation enabled */}
      <PresentationControls
        global={false}
        cursor={true}
        snap={false}
        speed={1.5}
        zoom={1}
        rotation={[0, 0, 0]}
        polar={[-Math.PI / 4, Math.PI / 4]} 
        azimuth={[-Infinity, Infinity]} 
      >
        <Float speed={1} rotationIntensity={0.05} floatIntensity={0.1} floatingRange={[-0.02, 0.02]}>
          <group position={[0, 0.2, 0]}>
            <TVModel 
              isPlaying={isPlaying} 
              onPlayPause={onPlayPause}
              onForward={onForward}
              onRewind={onRewind}
              onStop={onStop}
            />
          </group>
        </Float>
      </PresentationControls>

      {/* Floor Shadow */}
      <ContactShadows 
        position={[0, -1.8, 0]} 
        opacity={0.5} 
        scale={10} 
        blur={2.5} 
        far={4} 
        color="#000"
      />
    </>
  );
};

export default Scene;