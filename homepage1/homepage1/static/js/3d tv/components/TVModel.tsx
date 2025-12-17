import React, { useState, useMemo } from 'react';
import * as THREE from 'three';
import { RoundedBox } from '@react-three/drei';
import { ThreeEvent } from '@react-three/fiber';

interface TVModelProps {
  isPlaying: boolean;
  onPlayPause: () => void;
  onForward: () => void;
  onRewind: () => void;
  onStop: () => void;
}

// Colors
const THEME = {
  GOLD: "#E6C288",     // Champagne Gold
  GOLD_HIGH: "#FFF0D0", 
  NAVY: "#0A1A2F",     // Deep Royal Navy
  NAVY_LIGHT: "#152a45",
  SPEAKER_BLACK: "#111111"
};

// Reusable Front-Facing Button
const FrontButton = ({ 
  onClick, 
  position, 
  children,
  active = false,
  scale = 1
}: { 
  onClick: (e: ThreeEvent<MouseEvent>) => void, 
  position: [number, number, number], 
  children: React.ReactNode,
  active?: boolean,
  scale?: number
}) => {
  const [hovered, setHover] = useState(false);
  const [pressed, setPressed] = useState(false);
  
  return (
    <group position={position} scale={scale}>
      {/* Button Housing Ring */}
      <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
         <cylinderGeometry args={[0.08, 0.08, 0.01, 32]} />
         <meshStandardMaterial color={THEME.NAVY} roughness={0.5} />
      </mesh>

      {/* Button Cap */}
      <mesh 
        onClick={(e) => { e.stopPropagation(); onClick(e); }}
        onPointerOver={(e) => { e.stopPropagation(); setHover(true); }}
        onPointerOut={(e) => { e.stopPropagation(); setHover(false); }}
        onPointerDown={(e) => { e.stopPropagation(); setPressed(true); }}
        onPointerUp={(e) => { e.stopPropagation(); setPressed(false); }}
        rotation={[Math.PI / 2, 0, 0]} 
        position={[0, 0, pressed ? 0.005 : 0.015]} 
      >
        <cylinderGeometry args={[0.06, 0.065, 0.02, 32]} />
        <meshStandardMaterial 
          color={hovered ? "#ffffff" : "#eeeeee"} 
          roughness={0.2} 
          metalness={0.8} 
        />
        
        {/* Active Blue Light Ring */}
        {(active || pressed) && (
            <mesh position={[0, -0.011, 0]}>
                <cylinderGeometry args={[0.07, 0.07, 0.005, 32]} />
                <meshBasicMaterial color="#00aaff" toneMapped={false} />
            </mesh>
        )}
      </mesh>

      {/* Icon Geometry (Black on Metal) */}
      <group position={[0, 0, pressed ? 0.02 : 0.03]}>
         {children}
      </group>
    </group>
  );
};

// High-Fidelity Speaker Driver Component
const HiFiDriver = ({ position }: { position: [number, number, number] }) => (
    <group position={position}>
        {/* Outer Ring (Trim) - Removed rotation so it faces Front (Z) */}
        <mesh>
            <torusGeometry args={[0.12, 0.015, 16, 64]} />
            <meshStandardMaterial color="#444" metalness={0.8} roughness={0.2} />
        </mesh>
        
        {/* Surround (Rubber) */}
        <mesh position={[0,0,-0.01]}>
             <torusGeometry args={[0.10, 0.02, 16, 64]} />
             <meshStandardMaterial color="#111" roughness={0.6} />
        </mesh>

        {/* Cone (Deep Navy/Black) - Rotated to point Z forward */}
        <mesh rotation={[Math.PI/2, 0, 0]} position={[0,0,-0.02]}>
             <coneGeometry args={[0.10, 0.04, 64, 1, true]} />
             <meshStandardMaterial color="#080808" roughness={0.4} />
        </mesh>

        {/* Dust Cap (Gold Accent) */}
        <mesh position={[0,0,0.01]}>
             <sphereGeometry args={[0.035, 32, 32, 0, Math.PI * 2, 0, Math.PI/2]} />
             <meshStandardMaterial color={THEME.GOLD} metalness={0.9} roughness={0.2} />
        </mesh>
    </group>
)

const TVModel: React.FC<TVModelProps> = ({ 
  isPlaying, 
  onPlayPause,
  onForward,
  onRewind,
}) => {
  // Temporary state for button feedback
  const [rewindActive, setRewindActive] = useState(false);
  const [forwardActive, setForwardActive] = useState(false);

  const handleRewindClick = (e: any) => {
      setRewindActive(true);
      onRewind();
      setTimeout(() => setRewindActive(false), 200);
  };

  const handleForwardClick = (e: any) => {
      setForwardActive(true);
      onForward();
      setTimeout(() => setForwardActive(false), 200);
  };

  const screenTexture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 512;
    const ctx = canvas.getContext('2d');
    if (ctx) {
        // Sophisticated Navy Gradient
        const gradient = ctx.createLinearGradient(0, 0, 512, 512);
        gradient.addColorStop(0, '#020024'); 
        gradient.addColorStop(0.5, '#090979'); 
        gradient.addColorStop(1, '#00d4ff'); 
        ctx.fillStyle = gradient;
        ctx.fillRect(0,0,512,512);
        
        // Abstract Gold Circle
        ctx.lineWidth = 10;
        ctx.strokeStyle = "#E6C288";
        ctx.beginPath();
        ctx.arc(256, 256, 120, 0, Math.PI*2);
        ctx.stroke();
    }
    return new THREE.CanvasTexture(canvas);
  }, []);

  return (
    <group>
      {/* --- TV UNIT --- */}
      <group position={[0, 0.5, 0]}>
        
        {/* TV Frame - Deep Navy */}
        <RoundedBox args={[3.22, 1.92, 0.08]} radius={0.02} smoothness={4} receiveShadow castShadow>
          <meshStandardMaterial 
            color={THEME.NAVY} 
            roughness={0.2} 
            metalness={0.5} 
            envMapIntensity={1.2}
          />
        </RoundedBox>

        {/* Gold Trim Border (Thinner, Classier) */}
        <mesh position={[0, 0, 0.041]}>
            <boxGeometry args={[3.225, 1.925, 0.005]} />
            <meshStandardMaterial color={THEME.GOLD} metalness={1} roughness={0.1} />
        </mesh>
        
        {/* Active Border Glow */}
        {isPlaying && (
           <mesh position={[0, 0, 0.045]}>
              <boxGeometry args={[3.12, 1.82, 0.01]} />
              <meshBasicMaterial color="#4488ff" transparent opacity={0.15} toneMapped={false} />
           </mesh>
        )}

        {/* Back Panel */}
        <RoundedBox args={[3.0, 1.7, 0.15]} position={[0,0,-0.1]} radius={0.1} smoothness={4}>
           <meshStandardMaterial color={THEME.NAVY} roughness={0.8} />
        </RoundedBox>

        {/* The Screen */}
        <mesh position={[0, 0, 0.05]}>
          <planeGeometry args={[3.1, 1.8]} />
          {isPlaying ? (
            <meshStandardMaterial 
                map={screenTexture}
                emissiveMap={screenTexture}
                emissive="#ffffff"
                emissiveIntensity={0.6}
            />
          ) : (
            <meshStandardMaterial color="#000000" roughness={0.05} metalness={0.9} />
          )}
        </mesh>
        
        {/* Standby Light */}
         <mesh position={[1.5, -0.9, 0.06]}>
            <circleGeometry args={[0.005, 16]} />
            <meshBasicMaterial color={isPlaying ? "#00ff00" : "#ff0000"} toneMapped={false} />
        </mesh>

        {/* Ambilight */}
        {isPlaying && (
           <pointLight 
             position={[0, 0, 1.0]} 
             intensity={1.0} 
             distance={4} 
             color="#4488ff" 
             decay={2}
           />
        )}
      </group>


      {/* --- LUXURY SOUNDBAR SLIM REDESIGN --- */}
      {/* Position: Lowered TV is roughly at -0.46. Soundbar top needs to be near -0.5. */}
      {/* New Height 0.28. Y Center = -0.5 - (0.28/2) = -0.64 */}
      <group position={[0, -0.65, 0.2]}>
        
        {/* 1. Main Body (Slimmer Navy Cabinet) */}
        <RoundedBox args={[2.4, 0.28, 0.15]} radius={0.04} smoothness={8} castShadow receiveShadow>
            <meshStandardMaterial 
                color={THEME.NAVY} 
                roughness={0.4} 
                metalness={0.4}
            />
        </RoundedBox>

        {/* 2. Front Faceplate (Brushed Gold Aluminum) */}
        <mesh position={[0, 0, 0.076]}>
            <boxGeometry args={[2.35, 0.24, 0.01]} />
            <meshStandardMaterial 
                color={THEME.GOLD} 
                roughness={0.3} 
                metalness={0.9} 
                envMapIntensity={1.5}
            />
        </mesh>

        {/* 3. Speaker Drivers (Visible Hi-Fi Elements - Now Vertically Oriented) */}
        {/* Placed prominently on Left and Right of the Gold Face */}
        <group position={[0, 0, 0.08]}>
            <HiFiDriver position={[-0.9, 0, 0]} />
            <HiFiDriver position={[0.9, 0, 0]} />
             {/* Extra mid drivers for detail */}
            <HiFiDriver position={[-0.55, 0, 0]} />
            <HiFiDriver position={[0.55, 0, 0]} />
        </group>

        {/* 4. Center Control Cluster (The "Island") */}
        <group position={[0, 0, 0.08]}>
            {/* Control Panel Background (Navy Pill Shape) */}
            <mesh position={[0, 0, 0.005]}>
                 <boxGeometry args={[0.7, 0.16, 0.01]} />
                 <meshStandardMaterial color={THEME.NAVY_LIGHT} roughness={0.3} metalness={0.6} />
            </mesh>
            <mesh position={[-0.35, 0, 0.005]} rotation={[Math.PI/2, 0, 0]}>
                 <cylinderGeometry args={[0.08, 0.08, 0.01, 32]} />
                 <meshStandardMaterial color={THEME.NAVY_LIGHT} roughness={0.3} metalness={0.6} />
            </mesh>
            <mesh position={[0.35, 0, 0.005]} rotation={[Math.PI/2, 0, 0]}>
                 <cylinderGeometry args={[0.08, 0.08, 0.01, 32]} />
                 <meshStandardMaterial color={THEME.NAVY_LIGHT} roughness={0.3} metalness={0.6} />
            </mesh>

            {/* CONTROLS - Front and Center */}
            <group position={[0, 0, 0.01]}>
                
                {/* Rewind */}
                <FrontButton onClick={handleRewindClick} active={rewindActive} position={[-0.22, 0, 0]} scale={0.6}>
                   <group rotation={[0, 0, Math.PI / 2]} scale={0.6}>
                      <mesh position={[0, 0.015, 0]}>
                        <coneGeometry args={[0.02, 0.03, 3]} />
                        <meshBasicMaterial color="#333" />
                      </mesh>
                      <mesh position={[0, -0.015, 0]}>
                        <coneGeometry args={[0.02, 0.03, 3]} />
                        <meshBasicMaterial color="#333" />
                      </mesh>
                   </group>
                </FrontButton>

                {/* Play/Pause (Enlarged) */}
                <FrontButton onClick={onPlayPause} position={[0, 0, 0]} active={isPlaying} scale={0.9}>
                   {isPlaying ? (
                     <group>
                       <mesh position={[-0.015, 0, 0]}>
                          <boxGeometry args={[0.012, 0.04, 0.01]} />
                          <meshBasicMaterial color="#222" />
                       </mesh>
                       <mesh position={[0.015, 0, 0]}>
                           <boxGeometry args={[0.012, 0.04, 0.01]} />
                          <meshBasicMaterial color="#222" />
                       </mesh>
                     </group>
                   ) : (
                     <mesh rotation={[0, 0, -Math.PI/2]} position={[0.005, 0, 0]}>
                        <coneGeometry args={[0.025, 0.045, 3]} />
                        <meshBasicMaterial color="#222" />
                     </mesh>
                   )}
                </FrontButton>

                {/* Forward */}
                <FrontButton onClick={handleForwardClick} active={forwardActive} position={[0.22, 0, 0]} scale={0.6}>
                   <group rotation={[0, 0, -Math.PI / 2]} scale={0.6}>
                      <mesh position={[0, 0.015, 0]}>
                        <coneGeometry args={[0.02, 0.03, 3]} />
                        <meshBasicMaterial color="#333" />
                      </mesh>
                      <mesh position={[0, -0.015, 0]}>
                        <coneGeometry args={[0.02, 0.03, 3]} />
                        <meshBasicMaterial color="#333" />
                      </mesh>
                   </group>
                </FrontButton>
            </group>
        </group>

      </group>

    </group>
  );
};

export default TVModel;