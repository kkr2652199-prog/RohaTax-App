import React from 'react';
import { Box, Cylinder, RoundedBox } from '@react-three/drei';

interface ShowcaseProps {
  width: number;
  height: number;
  depth: number;
}

export const Showcase: React.FC<ShowcaseProps> = ({ width, height, depth }) => {
  const woodColor = "#1a0f05"; // Darker mahogany
  const goldColor = "#CFB53B"; // Champagne gold
  
  const frameThickness = 0.06;
  const legHeight = 4;
  
  return (
    <group position={[0, 0, 0]}>
      {/* --- Legs (Added as requested) --- */}
      {/* We position the legs below the main body. 
          The main body starts at -height/2. 
      */}
      <group position={[0, -height/2, 0]}>
         {/* Front Left */}
         <Cylinder args={[0.1, 0.05, legHeight, 16]} position={[-width/2 + 0.5, -legHeight/2, depth/2 - 0.5]}>
            <meshStandardMaterial color={goldColor} metalness={0.9} roughness={0.1} />
         </Cylinder>
         {/* Front Right */}
         <Cylinder args={[0.1, 0.05, legHeight, 16]} position={[width/2 - 0.5, -legHeight/2, depth/2 - 0.5]}>
            <meshStandardMaterial color={goldColor} metalness={0.9} roughness={0.1} />
         </Cylinder>
         {/* Back Left */}
         <Cylinder args={[0.1, 0.05, legHeight, 16]} position={[-width/2 + 0.5, -legHeight/2, -depth/2 + 0.5]}>
            <meshStandardMaterial color={goldColor} metalness={0.9} roughness={0.1} />
         </Cylinder>
         {/* Back Right */}
         <Cylinder args={[0.1, 0.05, legHeight, 16]} position={[width/2 - 0.5, -legHeight/2, -depth/2 + 0.5]}>
            <meshStandardMaterial color={goldColor} metalness={0.9} roughness={0.1} />
         </Cylinder>
      </group>

      {/* --- Base Cabinet --- */}
      {/* A thin elegant base for the glass to sit on */}
      <RoundedBox args={[width, 0.2, depth]} position={[0, -height/2 + 0.1, 0]} radius={0.05} smoothness={4}>
         <meshStandardMaterial color={woodColor} roughness={0.1} metalness={0.2} />
      </RoundedBox>

      {/* --- The Glass Display Area --- */}
      {/* Centered at 0 */}
      <group position={[0, 0, 0]}>
        
        {/* Floor of the display (Velvet Bed inside) */}
        <RoundedBox args={[width - 0.2, 0.1, depth - 0.2]} position={[0, -height/2 + 0.2, 0]} radius={0.1} smoothness={4}>
             <meshStandardMaterial color="#f0f0f0" roughness={0.9} />
        </RoundedBox>

        {/* --- Metal Frame (Curved/Cylindrical) --- */}
        
        {/* Vertical Pillars (Corners) */}
        <Cylinder args={[frameThickness, frameThickness, height, 16]} position={[-width/2 + frameThickness, 0, depth/2 - frameThickness]}>
           <meshStandardMaterial color={goldColor} metalness={0.95} roughness={0.1} />
        </Cylinder>
        <Cylinder args={[frameThickness, frameThickness, height, 16]} position={[width/2 - frameThickness, 0, depth/2 - frameThickness]}>
           <meshStandardMaterial color={goldColor} metalness={0.95} roughness={0.1} />
        </Cylinder>
        <Cylinder args={[frameThickness, frameThickness, height, 16]} position={[-width/2 + frameThickness, 0, -depth/2 + frameThickness]}>
           <meshStandardMaterial color={goldColor} metalness={0.95} roughness={0.1} />
        </Cylinder>
        <Cylinder args={[frameThickness, frameThickness, height, 16]} position={[width/2 - frameThickness, 0, -depth/2 + frameThickness]}>
           <meshStandardMaterial color={goldColor} metalness={0.95} roughness={0.1} />
        </Cylinder>

        {/* Top Frame constructed manually */}
        <RoundedBox args={[width, frameThickness*2, frameThickness*2]} position={[0, height/2, depth/2 - frameThickness]} radius={0.02} smoothness={4}>
             <meshStandardMaterial color={goldColor} metalness={0.95} roughness={0.1} />
        </RoundedBox>
        <RoundedBox args={[width, frameThickness*2, frameThickness*2]} position={[0, height/2, -depth/2 + frameThickness]} radius={0.02} smoothness={4}>
             <meshStandardMaterial color={goldColor} metalness={0.95} roughness={0.1} />
        </RoundedBox>
        <RoundedBox args={[frameThickness*2, frameThickness*2, depth]} position={[-width/2 + frameThickness, height/2, 0]} radius={0.02} smoothness={4}>
             <meshStandardMaterial color={goldColor} metalness={0.95} roughness={0.1} />
        </RoundedBox>
        <RoundedBox args={[frameThickness*2, frameThickness*2, depth]} position={[width/2 - frameThickness, height/2, 0]} radius={0.02} smoothness={4}>
             <meshStandardMaterial color={goldColor} metalness={0.95} roughness={0.1} />
        </RoundedBox>

        {/* Bottom Frame */}
        <RoundedBox args={[width, frameThickness*2, frameThickness*2]} position={[0, -height/2, depth/2 - frameThickness]} radius={0.02} smoothness={4}>
             <meshStandardMaterial color={goldColor} metalness={0.95} roughness={0.1} />
        </RoundedBox>
        <RoundedBox args={[width, frameThickness*2, frameThickness*2]} position={[0, -height/2, -depth/2 + frameThickness]} radius={0.02} smoothness={4}>
             <meshStandardMaterial color={goldColor} metalness={0.95} roughness={0.1} />
        </RoundedBox>
        <RoundedBox args={[frameThickness*2, frameThickness*2, depth]} position={[-width/2 + frameThickness, -height/2, 0]} radius={0.02} smoothness={4}>
             <meshStandardMaterial color={goldColor} metalness={0.95} roughness={0.1} />
        </RoundedBox>
        <RoundedBox args={[frameThickness*2, frameThickness*2, depth]} position={[width/2 - frameThickness, -height/2, 0]} radius={0.02} smoothness={4}>
             <meshStandardMaterial color={goldColor} metalness={0.95} roughness={0.1} />
        </RoundedBox>


        {/* The Glass Enclosure */}
        <RoundedBox args={[width - 0.05, height - 0.05, depth - 0.05]} radius={0.05} smoothness={4}>
          <meshPhysicalMaterial 
            transmission={0.98}  
            thickness={2.0}
            roughness={0.0}
            ior={1.5}
            color="#ffffff"
            attenuationColor="#eef"
            attenuationDistance={10}
            transparent={true}
            opacity={0.3}
            envMapIntensity={1.5}
          />
        </RoundedBox>

      </group>
    </group>
  );
};