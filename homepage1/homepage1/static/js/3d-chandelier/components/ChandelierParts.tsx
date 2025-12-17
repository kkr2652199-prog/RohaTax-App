import React, { useMemo } from 'react';
import * as THREE from 'three';
import { Cylinder, Sphere, Torus } from '@react-three/drei';

// Materials
export const metalMaterial = new THREE.MeshStandardMaterial({
  color: "#e8dcc0", // Pale gold/cream
  roughness: 0.2,
  metalness: 0.8,
});

export const crystalMaterial = new THREE.MeshPhysicalMaterial({
  color: "#dda520", // Amber/Goldenrod
  roughness: 0,
  metalness: 0,
  transmission: 0.9, // Glass-like transparency
  thickness: 2,
  ior: 1.5,
  clearcoat: 1,
});

export const fabricMaterial = new THREE.MeshStandardMaterial({
  color: "#fdf5e6", // Old Lace
  roughness: 0.8,
  side: THREE.DoubleSide,
});

interface ArmProps {
  rotation: number;
  lightIntensity: number;
  lightColor: string;
}

export const ChandelierArm: React.FC<ArmProps> = ({ rotation, lightIntensity, lightColor }) => {
  // Create a curved tube geometry for the arm using a CatmullRomCurve3
  const curve = useMemo(() => {
    // Defines the "S" / "U" shape of the arm
    const points = [
      new THREE.Vector3(0, 0, 0),         // Start at center hub
      new THREE.Vector3(0.5, -0.2, 0),    // Slightly out and down
      new THREE.Vector3(1.5, -2.5, 0),    // Deep swoop down
      new THREE.Vector3(3.5, -1.0, 0),    // Curve back up and out
      new THREE.Vector3(3.8, 0.5, 0),     // End point where shade sits
    ];
    return new THREE.CatmullRomCurve3(points);
  }, []);

  return (
    <group rotation={[0, rotation, 0]}>
      {/* The Metal Arm Tube */}
      <mesh material={metalMaterial} castShadow>
        <tubeGeometry args={[curve, 64, 0.08, 16, false]} />
      </mesh>

      {/* Connection to center (Decorative Ring) */}
      <mesh position={[0.4, 0, 0]} rotation={[0, 0, Math.PI / 2]} material={metalMaterial}>
        <torusGeometry args={[0.15, 0.04, 16, 32]} />
      </mesh>

      {/* The End Assembly (Crystal + Shade) */}
      <group position={[3.8, 0.5, 0]}>
        {/* Amber Crystal Ball decoration under the shade */}
        <group position={[0, -0.6, 0]}>
           {/* Metal stem holding crystal */}
           <mesh position={[0, 0.3, 0]} material={metalMaterial}>
              <cylinderGeometry args={[0.04, 0.04, 0.6, 8]} />
           </mesh>
           {/* The Amber Sphere */}
           <mesh material={crystalMaterial} castShadow>
              <sphereGeometry args={[0.35, 32, 32]} />
           </mesh>
           {/* Tiny finial at bottom of sphere */}
           <mesh position={[0, -0.4, 0]} material={metalMaterial}>
              <sphereGeometry args={[0.08, 16, 16]} />
           </mesh>
        </group>

        {/* The Candle Holder/Cup */}
        <mesh position={[0, 0, 0]} material={metalMaterial}>
           <cylinderGeometry args={[0.25, 0.1, 0.3, 32]} />
        </mesh>
        
        {/* Flower petal detail under shade */}
        <mesh position={[0, -0.1, 0]} rotation={[0, 0, 0]} material={metalMaterial}>
            <torusGeometry args={[0.2, 0.05, 16, 6]} />
        </mesh>

        {/* The Lamp Shade */}
        <group position={[0, 1.2, 0]}>
          <mesh material={fabricMaterial} castShadow>
            {/* Top radius, Bottom radius, Height, Segments */}
            <cylinderGeometry args={[0.6, 1.0, 2.0, 64, 1, true]} />
          </mesh>
          
          {/* Inner Light Source (Bulb) */}
          <pointLight 
            intensity={lightIntensity} 
            color={lightColor} 
            distance={5} 
            decay={2} 
            position={[0, 0, 0]}
            castShadow
          />
          {/* Visual Bulb (fake) */}
          <mesh position={[0, -0.2, 0]}>
            <sphereGeometry args={[0.15, 16, 16]} />
            <meshBasicMaterial color={lightColor} toneMapped={false} />
          </mesh>
        </group>
      </group>
    </group>
  );
};
