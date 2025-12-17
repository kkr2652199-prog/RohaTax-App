import React, { useMemo } from 'react';
import * as THREE from 'three';
import { Instances, Instance } from '@react-three/drei';

// --- Materials ---

const GOLD_MATERIAL = new THREE.MeshStandardMaterial({
  color: "#FFD700",
  metalness: 1,
  roughness: 0.15,
  envMapIntensity: 1.5,
  side: THREE.DoubleSide
});

// Upgraded Velvet Material - Deeper, flatter, more textile-like
const VELVET_MATERIAL = new THREE.MeshPhysicalMaterial({
  color: "#3d0000", // Deepest blood red for luxury
  roughness: 1.0,   // Fully rough (fabric has no specular highlights like plastic)
  metalness: 0.1,  
  sheen: 1.2,       // Soft sheen
  sheenRoughness: 0.5,
  sheenColor: "#ff1a1a", // Red sheen highlights
  clearcoat: 0.0,  // No clearcoat to avoid plastic look
  side: THREE.DoubleSide
});

const PEARL_MATERIAL = new THREE.MeshStandardMaterial({
  color: "#fffff0", // Cream white
  roughness: 0.3,
  metalness: 0.1,
});

// High Quality Diamond Material
const DIAMOND_MATERIAL = new THREE.MeshPhysicalMaterial({
  color: "#ffffff",
  metalness: 0.0,
  roughness: 0.0,
  transmission: 1.0, 
  thickness: 0.8,   
  ior: 2.4,          
  dispersion: 6,     
  clearcoat: 1.0,
  clearcoatRoughness: 0.0,
  envMapIntensity: 2.0,
  attenuationColor: new THREE.Color("#e6e6fa"),
  attenuationDistance: 1.0,
});

const SAPPHIRE_MATERIAL = new THREE.MeshPhysicalMaterial({
  color: "#0f2c6b",
  metalness: 0.1,
  roughness: 0.05,
  transmission: 0.6,
  thickness: 2,
  ior: 1.77,
});

const RUBY_MATERIAL = new THREE.MeshPhysicalMaterial({
  color: "#8a0303",
  metalness: 0.1,
  roughness: 0.05,
  transmission: 0.5,
  thickness: 2,
  ior: 1.76,
});

const EMERALD_MATERIAL = new THREE.MeshPhysicalMaterial({
  color: "#034b03",
  metalness: 0.1,
  roughness: 0.05,
  transmission: 0.5,
  thickness: 2,
  ior: 1.57,
});


// --- Helper Components ---

const RadialDistribution = ({ 
  count, 
  radius, 
  y = 0, 
  renderItem,
  startAngle = 0,
  arc = Math.PI * 2
}: { 
  count: number; 
  radius: number; 
  y?: number;
  startAngle?: number;
  arc?: number;
  renderItem: (i: number, pos: [number, number, number], rot: [number, number, number]) => React.ReactNode 
}) => {
  return (
    <group position={[0, y, 0]}>
      {Array.from({ length: count }).map((_, i) => {
        const angle = startAngle + (i / count) * arc;
        const x = Math.cos(angle) * radius;
        const z = Math.sin(angle) * radius;
        return renderItem(i, [x, 0, z], [0, -angle, 0]);
      })}
    </group>
  );
};

// --- Crown Parts ---

const BaseCirclet = () => {
  return (
    <group>
      {/* Main Band - Cylinder */}
      <mesh material={GOLD_MATERIAL} receiveShadow castShadow>
        <cylinderGeometry args={[2.5, 2.5, 1.2, 64]} />
      </mesh>
      
      {/* Top Rim - Enhanced for luxury */}
      <mesh material={GOLD_MATERIAL} position={[0, 0.65, 0]}>
        <cylinderGeometry args={[2.6, 2.6, 0.15, 64]} />
      </mesh>
      {/* Top Rim Detail */}
      <mesh material={GOLD_MATERIAL} position={[0, 0.65, 0]} rotation={[Math.PI/2, 0, 0]}>
        <torusGeometry args={[2.6, 0.05, 16, 64]} />
      </mesh>

      {/* Bottom Rim - Enhanced for luxury */}
      <mesh material={GOLD_MATERIAL} position={[0, -0.65, 0]}>
        <cylinderGeometry args={[2.6, 2.6, 0.15, 64]} />
      </mesh>
       {/* Bottom Rim Detail */}
       <mesh material={GOLD_MATERIAL} position={[0, -0.65, 0]} rotation={[Math.PI/2, 0, 0]}>
        <torusGeometry args={[2.6, 0.05, 16, 64]} />
      </mesh>

      {/* Decorative Panels on Band */}
      <RadialDistribution 
        count={8} 
        radius={2.52} 
        renderItem={(i, pos, rot) => (
          <group key={i} position={pos} rotation={rot}>
             {/* 1. Square Gem Frame (Bezel) */}
             <mesh material={GOLD_MATERIAL} position={[0, 0, 0]}>
                <boxGeometry args={[0.08, 0.55, 0.55]} />
             </mesh>

             {/* 2. The Main Gem - OVAL CUT (Luxurious, not sharp) */}
             <group position={[0.1, 0, 0]}>
                {/* Stone */}
                <mesh material={i % 2 === 0 ? RUBY_MATERIAL : EMERALD_MATERIAL} scale={[0.3, 1, 0.7]}>
                   {/* Dodecahedron gives a nice faceted round/oval look */}
                   <dodecahedronGeometry args={[0.25, 0]} />
                </mesh>
                
                {/* Gold Setting/Prongs */}
                <group>
                  <mesh material={GOLD_MATERIAL} position={[0, 0.2, 0.15]} rotation={[0.2, 0, 0]}>
                    <cylinderGeometry args={[0.02, 0.02, 0.1, 8]} />
                  </mesh>
                  <mesh material={GOLD_MATERIAL} position={[0, -0.2, 0.15]} rotation={[-0.2, 0, 0]}>
                    <cylinderGeometry args={[0.02, 0.02, 0.1, 8]} />
                  </mesh>
                  <mesh material={GOLD_MATERIAL} position={[0, 0.2, -0.15]} rotation={[0.2, 0, 0]}>
                    <cylinderGeometry args={[0.02, 0.02, 0.1, 8]} />
                  </mesh>
                  <mesh material={GOLD_MATERIAL} position={[0, -0.2, -0.15]} rotation={[-0.2, 0, 0]}>
                    <cylinderGeometry args={[0.02, 0.02, 0.1, 8]} />
                  </mesh>
                </group>
             </group>
             
             {/* Small Diamond accents - Faceted Pavé style */}
             <mesh material={DIAMOND_MATERIAL} position={[0.04, 0.42, 0.42]} scale={[1, 0.4, 1]}>
                <dodecahedronGeometry args={[0.06, 0]} />
             </mesh>
             <mesh material={DIAMOND_MATERIAL} position={[0.04, -0.42, 0.42]} scale={[1, 0.4, 1]}>
                <dodecahedronGeometry args={[0.06, 0]} />
             </mesh>
             <mesh material={DIAMOND_MATERIAL} position={[0.04, 0.42, -0.42]} scale={[1, 0.4, 1]}>
                <dodecahedronGeometry args={[0.06, 0]} />
             </mesh>
             <mesh material={DIAMOND_MATERIAL} position={[0.04, -0.42, -0.42]} scale={[1, 0.4, 1]}>
                <dodecahedronGeometry args={[0.06, 0]} />
             </mesh>
          </group>
        )}
      />
    </group>
  );
};

const Diamonds = () => {
  return (
    <group>
      {/* Top Row Diamonds - Pavé set */}
      <RadialDistribution 
        count={64} 
        radius={2.61} 
        y={0.65} 
        renderItem={(i, pos) => (
          <mesh key={`top-${i}`} position={pos} material={DIAMOND_MATERIAL} castShadow scale={[0.5, 0.5, 0.5]}>
            <dodecahedronGeometry args={[0.08, 0]} />
          </mesh>
        )} 
      />
      {/* Bottom Row Diamonds */}
      <RadialDistribution 
        count={64} 
        radius={2.61} 
        y={-0.65} 
        renderItem={(i, pos) => (
          <mesh key={`bottom-${i}`} position={pos} material={DIAMOND_MATERIAL} castShadow scale={[0.5, 0.5, 0.5]}>
            <dodecahedronGeometry args={[0.08, 0]} />
          </mesh>
        )} 
      />
    </group>
  );
};

const FleurDeLisSpikes = () => {
  return (
    <RadialDistribution 
      count={4} 
      radius={2.55} 
      y={0.7}
      startAngle={Math.PI / 4}
      renderItem={(i, pos, rot) => (
        <group key={i} position={pos} rotation={rot}>
           {/* Center Petal */}
           <mesh material={GOLD_MATERIAL} position={[0, 0.5, 0]} scale={[1, 1, 0.5]}>
             <capsuleGeometry args={[0.15, 0.6, 4, 8]} />
           </mesh>
           {/* Center Diamond Jewel */}
           <mesh material={DIAMOND_MATERIAL} position={[0.12, 0.5, 0]} scale={[0.6, 0.8, 0.6]}>
             <dodecahedronGeometry args={[0.12, 0]} />
           </mesh>

           {/* Side Scrolls */}
           <group position={[0, 0.3, 0]}>
             <mesh material={GOLD_MATERIAL} position={[0, 0, 0.25]} rotation={[0.5, 0, 0]}>
                <torusGeometry args={[0.15, 0.05, 8, 16, Math.PI * 1.5]} />
             </mesh>
             <mesh material={GOLD_MATERIAL} position={[0, 0, -0.25]} rotation={[-0.5, 0, 0]}>
                <torusGeometry args={[0.15, 0.05, 8, 16, Math.PI * 1.5]} />
             </mesh>
           </group>

           {/* Base connection */}
           <mesh material={GOLD_MATERIAL} position={[0, 0.1, 0]}>
             <cylinderGeometry args={[0.2, 0.25, 0.2, 8]} />
           </mesh>
        </group>
      )}
    />
  );
};

const VelvetCap = () => {
  // Tweaked: Confined within gold frame, raised height for luxury, clearer separation from arches
  return (
    <group position={[0, 0, 0]}>
        {/* 1. Base Cylinder - STRICTLY smaller than band (Band ID ~2.5) */}
        <mesh material={VELVET_MATERIAL} position={[0, 0, 0]}>
             <cylinderGeometry args={[2.3, 2.3, 1.2, 64]} />
        </mesh>

        {/* 2. The Puffy Top - Raised & Plush */}
        <group position={[0, 0.6, 0]}>
           {/* 4 Lobes in quadrants */}
           {[45, 135, 225, 315].map((deg) => (
             <group key={deg} rotation={[0, THREE.MathUtils.degToRad(deg), 0]}>
               {/* 
                  Position closer to center (x=0.6) to avoid burying the arches.
                  Scale Y=0.8 for height/plushness.
               */}
               <mesh material={VELVET_MATERIAL} position={[0.6, 0.1, 0]} scale={[1.1, 0.8, 1.1]}>
                 <sphereGeometry args={[1.1, 48, 32]} />
               </mesh>
             </group>
           ))}
           
           {/* Central Filler Dome - Slightly taller to peak */}
           <mesh material={VELVET_MATERIAL} position={[0, 0.3, 0]} scale={[1, 0.85, 1]}>
              <sphereGeometry args={[1.35, 48, 32]} />
           </mesh>
        </group>
    </group>
  );
}

const SingleArch = () => {
  // Increased radius to ensure it clears the velvet and looks structural
  const arcRadius = 2.55; 
  const numPearls = 15;
  
  return (
    <group>
        {/* Gold Strap - Thicker */}
        <mesh material={GOLD_MATERIAL} scale={[1, 0.85, 0.2]}>
           <torusGeometry args={[arcRadius, 0.25, 16, 64, Math.PI]} /> 
        </mesh>

        {/* Gold Piping (Edges) */}
        <group scale={[1, 0.85, 1]}>
            <mesh material={GOLD_MATERIAL} position={[0, 0, 0.15]}>
               <torusGeometry args={[arcRadius, 0.04, 8, 64, Math.PI]} /> 
            </mesh>
            <mesh material={GOLD_MATERIAL} position={[0, 0, -0.15]}>
               <torusGeometry args={[arcRadius, 0.04, 8, 64, Math.PI]} /> 
            </mesh>
        </group>

        {/* Pearls along the spine */}
        <Instances range={numPearls} material={PEARL_MATERIAL}>
            <sphereGeometry args={[0.09, 16, 16]} />
            {Array.from({ length: numPearls }).map((_, i) => {
                 const t = i / (numPearls - 1);
                 // Adjust range to not hit the bottom rim exactly
                 const adjustedAngle = 0.2 + t * (Math.PI - 0.4);
                 const x = Math.cos(adjustedAngle) * arcRadius;
                 const y = Math.sin(adjustedAngle) * arcRadius * 0.85; 
                 return <Instance key={i} position={[x, y, 0]} />;
            })}
        </Instances>
    </group>
  )
}

const CrossArches = () => {
  return (
    <group position={[0, 0.5, 0]} rotation={[0, Math.PI / 4, 0]}>
       {/* Arch 1: Spans X axis */}
       <SingleArch />
       
       {/* Arch 2: Spans Z axis (Rotated 90 deg) */}
       <group rotation={[0, Math.PI/2, 0]}>
         <SingleArch />
       </group>
       
       {/* Central Intersection Ornament (Monde Base) - More prominent */}
       <group position={[0, 2.55 * 0.85, 0]}>
         <mesh material={GOLD_MATERIAL}>
            <cylinderGeometry args={[0.45, 0.45, 0.2, 32]} />
         </mesh>
         <mesh material={GOLD_MATERIAL} position={[0, 0.15, 0]} rotation={[Math.PI/2, 0, 0]}>
            <torusGeometry args={[0.25, 0.06, 16, 32]} />
         </mesh>
         {/* Top Cross/Diamond */}
         <mesh material={DIAMOND_MATERIAL} position={[0, 0.4, 0]} rotation={[Math.PI/4, Math.PI/4, 0]} scale={[1, 1.2, 1]}>
            <dodecahedronGeometry args={[0.25, 0]} />
         </mesh>
       </group>
    </group>
  );
};

export const ImperialCrown: React.FC = () => {
  return (
    <group>
      <BaseCirclet />
      <Diamonds />
      <FleurDeLisSpikes />
      <VelvetCap />
      <CrossArches />
    </group>
  );
};