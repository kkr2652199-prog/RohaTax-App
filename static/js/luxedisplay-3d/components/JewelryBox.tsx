import React, { useRef, useState } from 'react';
import { Cylinder } from '@react-three/drei';
import { Mesh } from 'three';

interface JewelryBoxProps {
  position: [number, number, number];
  color?: string; // Kept for interface compatibility but we'll use gold defaults
}

export const JewelryBox: React.FC<JewelryBoxProps> = ({ position }) => {
  const [hovered, setHover] = useState(false);
  
  // Dimensions
  const height = 0.7; // Increased height
  const topRadius = 0.6;
  const bottomRadius = 0.7;

  return (
    <group position={position}>
      {/* Main Round Stand (Gold Body) */}
      <Cylinder
        args={[topRadius, bottomRadius, height, 64]}
        onPointerOver={() => setHover(true)}
        onPointerOut={() => setHover(false)}
      >
        <meshStandardMaterial
          color={hovered ? "#EAD9A6" : "#D4AF37"} // Gold colors
          roughness={0.2} 
          metalness={1.0}
          envMapIntensity={1.5}
        />
      </Cylinder>
      
      {/* Bottom Detail Ring */}
      <Cylinder args={[bottomRadius + 0.02, bottomRadius + 0.02, 0.05, 64]} position={[0, -height/2 + 0.025, 0]}>
         <meshStandardMaterial color="#AA8C2C" metalness={1} roughness={0.3} />
      </Cylinder>

      {/* Top Pad (Black Velvet for contrast) */}
      <mesh position={[0, height/2 + 0.001, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[topRadius - 0.05, 64]} />
        <meshStandardMaterial color="#1a1a1a" roughness={0.9} />
      </mesh>
    </group>
  );
};