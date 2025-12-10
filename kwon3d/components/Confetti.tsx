import React, { useMemo, useRef, useEffect, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Group, MathUtils, Vector3, Euler } from 'three';

const COLORS = ['#FFD700', '#FF0000', '#FFFFFF', '#00FF00', '#0000FF'];

interface ParticleData {
  position: Vector3;
  velocity: Vector3;
  rotation: Euler;
  rotVelocity: [number, number, number];
  scale: number;
  color: string;
}

interface ConfettiProps {
  explode: boolean;
}

export const Confetti: React.FC<ConfettiProps> = ({ explode }) => {
  const count = 80;
  const groupRef = useRef<Group>(null);
  const [particles, setParticles] = useState<ParticleData[]>([]);
  const [active, setActive] = useState(false);

  // Initialize particles
  useEffect(() => {
    if (explode) {
      const newParticles: ParticleData[] = [];
      for (let i = 0; i < count; i++) {
        // Start from center of the box
        const position = new Vector3((Math.random() - 0.5) * 1.5, -0.5, (Math.random() - 0.5) * 1.5);
        
        // Explode upwards and outwards
        const velocity = new Vector3(
          (Math.random() - 0.5) * 0.15, // Spread X
          Math.random() * 0.25 + 0.1,   // Upward force Y
          (Math.random() - 0.5) * 0.15  // Spread Z
        );

        newParticles.push({
          position,
          velocity,
          rotation: new Euler(Math.random() * Math.PI, Math.random() * Math.PI, 0),
          rotVelocity: [Math.random() * 0.2, Math.random() * 0.2, Math.random() * 0.2],
          scale: Math.random() * 0.1 + 0.05,
          color: COLORS[Math.floor(Math.random() * COLORS.length)],
        });
      }
      setParticles(newParticles);
      setActive(true);
    } else {
      // Reset when closed (hide particles)
      setActive(false);
      setParticles([]);
    }
  }, [explode]);

  useFrame(() => {
    if (!active || !groupRef.current) return;

    // Update particle physics manually for performance
    groupRef.current.children.forEach((mesh, i) => {
      const p = particles[i];
      if (!p) return;

      // Apply Gravity
      p.velocity.y -= 0.005; 
      
      // Update Position
      mesh.position.x += p.velocity.x;
      mesh.position.y += p.velocity.y;
      mesh.position.z += p.velocity.z;

      // Update Rotation
      mesh.rotation.x += p.rotVelocity[0];
      mesh.rotation.y += p.rotVelocity[1];
      mesh.rotation.z += p.rotVelocity[2];

      // Fade out or stop if too low? (Optional, visually simple to just let them fall through table)
    });
  });

  if (!active) return null;

  return (
    <group ref={groupRef}>
      {particles.map((p, i) => (
        <mesh key={i} position={p.position} rotation={p.rotation} castShadow>
          <planeGeometry args={[p.scale, p.scale]} />
          <meshStandardMaterial color={p.color} side={2} />
        </mesh>
      ))}
    </group>
  );
};