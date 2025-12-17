import React, { useRef } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { OrbitControls, Environment, ContactShadows } from '@react-three/drei';
import { EffectComposer, Bloom, Vignette } from '@react-three/postprocessing';
import { ChandelierArm, metalMaterial, crystalMaterial } from './ChandelierParts';
import { ChandelierProps } from '../types';

export const ChandelierScene: React.FC<ChandelierProps> = ({ lightState }) => {
  const groupRef = useRef<THREE.Group>(null);

  // Slow rotation for presentation
  useFrame((state, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.05;
    }
  });

  const numArms = 8;
  const arms = Array.from({ length: numArms }).map((_, i) => {
    const angle = (i / numArms) * Math.PI * 2;
    return (
      <ChandelierArm
        key={i}
        rotation={angle}
        lightIntensity={lightState.intensity}
        lightColor={lightState.lightColor}
      />
    );
  });

  return (
    <>
      <OrbitControls 
        minPolarAngle={0} 
        maxPolarAngle={Math.PI / 1.5} 
        enablePan={false}
        minDistance={5}
        maxDistance={15}
      />

      {/* Environment for reflections on metal/glass */}
      <Environment preset="lobby" />

      {/* Ambient Light for base visibility */}
      <ambientLight intensity={0.2} />

      {/* Main Chandelier Group */}
      <group ref={groupRef} position={[0, 2, 0]}>
        
        {/* Central Column Assembly */}
        <group>
            {/* Main Center Rod */}
            <mesh material={metalMaterial} position={[0, 1, 0]}>
                <cylinderGeometry args={[0.15, 0.15, 6, 32]} />
            </mesh>

            {/* Decorative Central Cluster (Vertical Rods) simulating the image detail */}
            {Array.from({ length: 6 }).map((_, i) => (
                <mesh key={i} material={metalMaterial} position={[
                    Math.cos((i/6)*Math.PI*2) * 0.25, 
                    1, 
                    Math.sin((i/6)*Math.PI*2) * 0.25
                ]}>
                    <cylinderGeometry args={[0.04, 0.04, 5, 16]} />
                </mesh>
            ))}

            {/* Top Loop/Chain Connector */}
            <mesh position={[0, 4, 0]} material={metalMaterial}>
                <torusGeometry args={[0.3, 0.08, 16, 32]} />
            </mesh>
            
            {/* Chain going up */}
            {Array.from({ length: 5 }).map((_, i) => (
               <mesh key={`chain-${i}`} position={[0, 4.5 + (i * 0.6), 0]} rotation={[0, i % 2 === 0 ? 0 : Math.PI/2, 0]} material={metalMaterial}>
                   <torusGeometry args={[0.2, 0.05, 16, 16]} />
               </mesh>
            ))}

            {/* Central Hub where arms connect */}
            <mesh position={[0, 0, 0]} material={metalMaterial}>
                <cylinderGeometry args={[0.6, 0.5, 0.8, 32]} />
            </mesh>

            {/* Bottom Crystal Finial */}
            <group position={[0, -4, 0]}>
                 {/* Long thin rod going down to finial */}
                 <mesh position={[0, 2, 0]} material={metalMaterial}>
                    <cylinderGeometry args={[0.05, 0.02, 4, 16]} />
                 </mesh>
                 {/* The Amber Finial */}
                 <mesh position={[0, 0, 0]} material={crystalMaterial} castShadow>
                     <sphereGeometry args={[0.5, 32, 32]} />
                 </mesh>
                 <mesh position={[0, -0.6, 0]} material={metalMaterial}>
                     <coneGeometry args={[0.1, 0.3, 16]} />
                 </mesh>
            </group>
        </group>

        {/* Arms */}
        {arms}
      </group>

      {/* Shadow Catcher */}
      <ContactShadows 
        opacity={0.6} 
        scale={20} 
        blur={2} 
        far={10} 
        resolution={256} 
        color="#000000" 
        position={[0, -5, 0]}
      />

      {/* Post Processing for the "Beautiful" Look */}
      <EffectComposer enableNormalPass={false}>
        {/* Bloom creates the glow around the shades and light bulbs */}
        <Bloom 
            luminanceThreshold={0.8} 
            mipmapBlur 
            intensity={1.2} 
            radius={0.6} 
        />
        <Vignette eskil={false} offset={0.1} darkness={1.1} />
      </EffectComposer>
    </>
  );
};