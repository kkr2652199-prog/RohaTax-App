
import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Group, MathUtils, Shape, ExtrudeGeometry } from 'three';
import { RoundedBox, Text } from '@react-three/drei';
import { Confetti } from './Confetti';

// Luxurious Colors
const BOX_RED = "#7f1d1d"; // Deep Royal Red
const RIBBON_GOLD = "#fbbf24"; // Bright Gold
const RIBBON_ACCENT = "#b45309"; // Dark Gold
const TEXT_COLOR = "#ffedcc"; // Soft Cream Gold

interface GiftModelProps {
  isOpen: boolean;
}

export const GiftHandModel: React.FC<GiftModelProps> = ({ isOpen }) => {
  const lidGroupRef = useRef<Group>(null);
  
  // Dimensions
  const boxWidth = 2.0;
  const boxDepth = 2.0;
  const boxHeight = 1.8;
  const wallThickness = 0.15;
  const ribbonWidth = 0.3;
  const ribbonThick = 0.02; 
  
  const lidHeight = 0.4;
  const lidOverhang = 0.1;
  
  // Corner Softness
  const boxRadius = 0.1; 
  const bevelSize = 0.03; 
  
  // Hinge logic
  const hingePosition: [number, number, number] = [0, boxHeight, -boxDepth / 2];

  // --- Create Seamless Hollow Box Geometry ---
  const boxGeometry = useMemo(() => {
    const shape = new Shape();
    const w = boxWidth / 2;
    const h = boxDepth / 2;
    const r = boxRadius;

    // Outer Rounded Rectangle
    shape.moveTo(-w + r, -h);
    shape.lineTo(w - r, -h);
    shape.quadraticCurveTo(w, -h, w, -h + r);
    shape.lineTo(w, h - r);
    shape.quadraticCurveTo(w, h, w - r, h);
    shape.lineTo(-w + r, h);
    shape.quadraticCurveTo(-w, h, -w, h - r);
    shape.lineTo(-w, -h + r);
    shape.quadraticCurveTo(-w, -h, -w + r, -h);

    // Inner Hole
    const hole = new Shape();
    const iw = w - wallThickness;
    const ih = h - wallThickness;
    const ir = Math.max(0.01, r - wallThickness);

    hole.moveTo(-iw + ir, -ih);
    hole.quadraticCurveTo(-iw, -ih, -iw, -ih + ir);
    hole.lineTo(-iw, ih - ir);
    hole.quadraticCurveTo(-iw, ih, -iw + ir, ih);
    hole.lineTo(iw - ir, ih);
    hole.quadraticCurveTo(iw, ih, iw, ih - ir);
    hole.lineTo(iw, -ih + ir);
    hole.quadraticCurveTo(iw, -ih, iw - ir, -ih);
    hole.lineTo(-iw + ir, -ih);

    shape.holes.push(hole);

    const extrudeSettings = {
      depth: boxHeight,
      bevelEnabled: true,
      bevelSegments: 5, 
      steps: 1,
      bevelSize: bevelSize,
      bevelThickness: bevelSize,
      curveSegments: 12 
    };

    return new ExtrudeGeometry(shape, extrudeSettings);
  }, []);

  useFrame((state, delta) => {
    if (lidGroupRef.current) {
      const targetRotation = isOpen ? -Math.PI * 0.65 : 0;
      lidGroupRef.current.rotation.x = MathUtils.lerp(
        lidGroupRef.current.rotation.x,
        targetRotation,
        delta * 3
      );
    }
  });

  // Helper component for Volumetric Text (Standard Font)
  const VolumetricText = ({ children, color = TEXT_COLOR, fontSize, ...props }: any) => {
    const layers = 5;
    const depth = 0.003;
    return (
      <group>
        {/* Shadow/Side Layers */}
        {Array.from({ length: layers }).map((_, i) => (
          <Text
            key={i}
            fontSize={fontSize}
            {...props}
            position={[0, 0, - (i + 1) * depth]}
            color="#3a0d0d" // Richer deep shadow
            fillOpacity={1}
            outlineWidth={0.002}
            outlineColor="#2a0505"
          >
            {children}
          </Text>
        ))}
        {/* Front Face */}
        <Text 
          fontSize={fontSize}
          {...props} 
          color={color}
        >
           {children}
           <meshPhysicalMaterial 
             color={color} 
             roughness={0.3} 
             metalness={0.1} 
             clearcoat={0.5}
             emissive={color}
             emissiveIntensity={0.25} 
           />
        </Text>
      </group>
    );
  };

  return (
    <group dispose={null} scale={[1.5, 1.5, 1.5]}> 
      
      {/* Confetti Explosion */}
      <group position={[0, boxHeight * 0.2, 0]}>
         <Confetti explode={isOpen} />
      </group>

      {/* --- STATIC BOTTOM BASE --- */}
      <group position={[0, 0, 0]}>
        
        {/* Seamless Walls */}
        <mesh 
          geometry={boxGeometry} 
          rotation={[-Math.PI / 2, 0, 0]} 
          position={[0, 0, 0]} 
          castShadow 
          receiveShadow
        >
          <meshPhysicalMaterial 
            color={BOX_RED} 
            roughness={0.25} 
            metalness={0.1} 
            clearcoat={0.8}
            clearcoatRoughness={0.2}
          />
        </mesh>

        {/* Floor */}
        <RoundedBox 
          args={[boxWidth - wallThickness * 2, wallThickness, boxDepth - wallThickness * 2]} 
          radius={0.05} 
          smoothness={4}
          position={[0, wallThickness / 2, 0]} 
          receiveShadow
        >
          <meshPhysicalMaterial 
            color={BOX_RED} 
            roughness={0.3} 
            metalness={0.1} 
          />
        </RoundedBox>
        
        {/* Exterior Ribbons */}
        <mesh position={[0, -ribbonThick/2, 0]} receiveShadow>
           <boxGeometry args={[ribbonWidth, ribbonThick, boxDepth - 0.2]} />
           <meshPhysicalMaterial color={RIBBON_GOLD} metalness={0.6} roughness={0.3} />
        </mesh>
        <mesh position={[0, -ribbonThick/2, 0]} receiveShadow>
           <boxGeometry args={[boxWidth - 0.2, ribbonThick, ribbonWidth]} />
           <meshPhysicalMaterial color={RIBBON_GOLD} metalness={0.6} roughness={0.3} />
        </mesh>

        {/* Vertical Side Ribbons */}
        <mesh position={[-boxWidth/2 - ribbonThick/2 + bevelSize, boxHeight/2, 0]} castShadow>
          <boxGeometry args={[ribbonThick, boxHeight, ribbonWidth]} />
          <meshPhysicalMaterial color={RIBBON_GOLD} metalness={0.6} roughness={0.3} />
        </mesh>
        <mesh position={[boxWidth/2 + ribbonThick/2 - bevelSize, boxHeight/2, 0]} castShadow>
          <boxGeometry args={[ribbonThick, boxHeight, ribbonWidth]} />
          <meshPhysicalMaterial color={RIBBON_GOLD} metalness={0.6} roughness={0.3} />
        </mesh>
        <mesh position={[0, boxHeight/2, -boxDepth/2 - ribbonThick/2 + bevelSize]} castShadow>
           <boxGeometry args={[ribbonWidth, boxHeight, ribbonThick]} />
           <meshPhysicalMaterial color={RIBBON_GOLD} metalness={0.6} roughness={0.3} />
        </mesh>
        <mesh position={[0, boxHeight/2, boxDepth/2 + ribbonThick/2 - bevelSize]} castShadow>
           <boxGeometry args={[ribbonWidth, boxHeight, ribbonThick]} />
           <meshPhysicalMaterial color={RIBBON_GOLD} metalness={0.6} roughness={0.3} />
        </mesh>

        {/* --- FRONT TEXT (PREMIUM AD LAYOUT) --- */}
        <group position={[0, boxHeight/2, boxDepth/2 + 0.07]}>
           
           {/* Top Title - Large, Spaced, Serif */}
           <group position={[0, 0.62, 0]}>
             <VolumetricText 
               fontSize={0.19} 
               color="#ffdb4d" 
               anchorX="center" 
               anchorY="middle"
               letterSpacing={0.05}
               fontWeight="bold"
             >
               🎉 토큰 이벤트
             </VolumetricText>
           </group>

           {/* Subtitle - Elegant */}
           <group position={[0, 0.44, 0]}>
             <VolumetricText 
               fontSize={0.11} 
               color="#ffe6b3" 
               anchorX="center" 
               anchorY="middle"
               letterSpacing={0.1}
             >
               Welcome Event
             </VolumetricText>
           </group>

           {/* MAIN BENEFIT - Maximum Impact */}
           <group position={[0, 0.15, 0]}>
             <VolumetricText 
               fontSize={0.18} 
               color="#ffffff" 
               anchorX="center" 
               anchorY="middle"
               fontWeight="bold"
             >
               신규 가입 혜택 (60토큰)
             </VolumetricText>
           </group>

           {/* Description 1 - Clear & Readable */}
           <group position={[0, -0.25, 0]}>
             <VolumetricText 
               fontSize={0.11} 
               color="#ffedcc" 
               anchorX="center" 
               anchorY="middle"
               lineHeight={1.4}
               textAlign="center"
             >
               {`60개의 무료 토큰이\n즉시 지급됩니다.`}
             </VolumetricText>
           </group>

           {/* Footer - Subtle */}
           <group position={[0, -0.65, 0]}>
             <VolumetricText 
               fontSize={0.095} 
               color="#ffca80" 
               anchorX="center" 
               anchorY="middle"
               lineHeight={1.5}
               textAlign="center"
             >
               {`금액 부담 없이 즉시 사용\n관리자 승인 없이 자동 적용`}
             </VolumetricText>
           </group>

        </group>

      </group>


      {/* --- ANIMATED LID (Hinged) --- */}
      <group position={hingePosition} ref={lidGroupRef}>
        <group position={[0, lidHeight / 2, boxDepth / 2]}>
          
          {/* Lid Mesh */}
          <RoundedBox 
            args={[boxWidth + lidOverhang, lidHeight, boxDepth + lidOverhang]} 
            radius={boxRadius} 
            smoothness={4}
          >
             <meshPhysicalMaterial 
              color={BOX_RED} 
              roughness={0.25} 
              metalness={0.1} 
              clearcoat={0.8}
            />
          </RoundedBox>

          {/* Lid Ribbons */}
           <mesh position={[0, 0, 0]}>
            <boxGeometry args={[ribbonWidth + 0.02, lidHeight + 0.01, boxDepth + lidOverhang + 0.02]} />
            <meshPhysicalMaterial color={RIBBON_GOLD} metalness={0.6} roughness={0.3} />
          </mesh>
           <mesh position={[0, 0, 0]}>
            <boxGeometry args={[boxWidth + lidOverhang + 0.02, lidHeight + 0.01, ribbonWidth + 0.02]} />
            <meshPhysicalMaterial color={RIBBON_GOLD} metalness={0.6} roughness={0.3} />
          </mesh>

          {/* --- THE BOW --- */}
           <group position={[0, lidHeight/2 + 0.1, 0]}>
             {/* Loops */}
            <mesh position={[-0.35, 0.15, 0]} rotation={[0, 0, 0.6]}>
               <torusGeometry args={[0.3, 0.12, 16, 32]} />
               <meshStandardMaterial color={RIBBON_GOLD} metalness={0.4} roughness={0.4} />
            </mesh>
            <mesh position={[0.35, 0.15, 0]} rotation={[0, 0, -0.6]}>
               <torusGeometry args={[0.3, 0.12, 16, 32]} />
               <meshStandardMaterial color={RIBBON_GOLD} metalness={0.4} roughness={0.4} />
            </mesh>
            
            {/* Center Knot */}
            <mesh position={[0, 0.05, 0]}>
              <sphereGeometry args={[0.18, 16, 16]} />
               <meshStandardMaterial color={RIBBON_ACCENT} metalness={0.4} roughness={0.4} />
            </mesh>

             {/* Ribbon Tails */}
             <group position={[-0.4, 0, 0.4]} rotation={[0.5, 0.5, 0]}>
                <mesh castShadow>
                   <boxGeometry args={[0.15, 0.8, 0.02]} />
                   <meshStandardMaterial color={RIBBON_GOLD} metalness={0.4} roughness={0.4} side={2} />
                </mesh>
             </group>
              <group position={[0.4, 0, -0.4]} rotation={[-0.5, -0.5, 0]}>
                <mesh castShadow>
                   <boxGeometry args={[0.15, 0.8, 0.02]} />
                   <meshStandardMaterial color={RIBBON_GOLD} metalness={0.4} roughness={0.4} side={2} />
                </mesh>
             </group>
          </group>

        </group>
      </group>

    </group>
  );
};
