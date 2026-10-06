'use client';

import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface BrainCanvasProps {
  reducedMotion?: boolean;
  mouseX?: React.MutableRefObject<number>;
  mouseY?: React.MutableRefObject<number>;
}

// Circular particle texture generator for glowing neural synaptic nodes
function createGlowTexture(colorHex: string) {
  if (typeof document === 'undefined') return null;
  const canvas = document.createElement('canvas');
  canvas.width = 64;
  canvas.height = 64;
  const ctx = canvas.getContext('2d')!;

  const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  gradient.addColorStop(0, '#ffffff');
  gradient.addColorStop(0.25, colorHex);
  gradient.addColorStop(0.65, `${colorHex}44`);
  gradient.addColorStop(1, 'rgba(0,0,0,0)');

  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 64, 64);

  return new THREE.CanvasTexture(canvas);
}

export function AnatomicalNeuralBrain({
  reducedMotion = false,
  mouseX,
  mouseY,
}: BrainCanvasProps) {
  const mainGroupRef = useRef<THREE.Group>(null);
  const cortexMeshRef = useRef<THREE.Mesh>(null);
  const neuralNodesRef = useRef<THREE.Points>(null);
  const failureNodesRef = useRef<THREE.Points>(null);
  const scanPlaneRef = useRef<THREE.Mesh>(null);
  const impulsePointsRef = useRef<THREE.Points>(null);

  // Textures for cyan and red synaptic glowing nodes
  const cyanGlowTexture = useMemo(() => createGlowTexture('#00f0ff'), []);
  const redGlowTexture = useMemo(() => createGlowTexture('#ef4444'), []);

  // 1. Build Anatomical Parametric Cortex Geometry
  const { cortexGeometry, neuralPoints, neuralLines, failurePoints, impulseData } = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    const vertices: number[] = [];
    const normals: number[] = [];
    const uvs: number[] = [];
    const indices: number[] = [];

    // Helper: evaluate realistic anatomical displacement for point (x, y, z)
    function getAnatomicalSurface(u: number, v: number, hemisphere: 1 | -1) {
      const theta = u * Math.PI; // 0 to PI
      const phi = v * Math.PI * 2.0; // 0 to 2PI

      // Ellipsoidal base coordinates: X=0.88, Y=0.82, Z=1.18
      const cosTheta = Math.cos(theta);
      const sinTheta = Math.sin(theta);
      const cosPhi = Math.cos(phi);
      const sinPhi = Math.sin(phi);

      let x = sinTheta * cosPhi * 0.88;
      let y = cosTheta * 0.82;
      let z = sinTheta * sinPhi * 1.18;

      // Hemispheric separation: offset along X axis with longitudinal fissure dip
      x = x * 0.85 + hemisphere * 0.12;

      // Temporal lobe bulge (inferior lateral anterior)
      if (y < 0.1 && y > -0.5 && z > 0.0) {
        x += hemisphere * 0.14 * (1.0 - Math.abs(y + 0.2) / 0.3);
      }

      // Frontal lobe rounding (positive Z)
      if (z > 0.6) {
        x *= 0.92;
        y *= 0.95;
      }

      // Occipital lobe taper (negative Z)
      if (z < -0.5) {
        x *= 0.9;
        y *= 0.88;
      }

      // Cerebellum (posterior-inferior: z < -0.2, y < -0.3)
      const isCerebellum = z < -0.15 && y < -0.35;
      if (isCerebellum) {
        const cerebellumFold = Math.sin(y * 42.0) * 0.035;
        x += hemisphere * 0.04 + cerebellumFold;
        y -= 0.12;
        z -= 0.08;
      }

      // Gyri & Sulci folds via multi-harmonic trigonometric displacement
      const foldFreq1 = 12.0;
      const foldFreq2 = 18.0;
      const fold1 = Math.sin(x * foldFreq1 + y * 4.0) * Math.cos(z * foldFreq1 * 0.8);
      const fold2 = Math.cos(y * foldFreq2) * Math.sin(z * foldFreq2 * 0.9 + x * 6.0);
      const fold3 = Math.sin((x * x + z * z) * 16.0);

      const sulcusCleft = Math.min(0, Math.sin(x * 10.0 + z * 8.0) * 0.06);
      const gyrusRidge = Math.max(0, (fold1 * 0.5 + fold2 * 0.35 + fold3 * 0.15) * 0.12);

      const totalDisplacement = isCerebellum
        ? 0
        : (gyrusRidge + sulcusCleft);

      // Apply displacement along radial normal
      const len = Math.sqrt(x * x + y * y + z * z) || 1;
      x += (x / len) * totalDisplacement;
      y += (y / len) * totalDisplacement;
      z += (z / len) * totalDisplacement;

      return new THREE.Vector3(x, y, z);
    }

    // Grid resolution for each hemisphere
    const uSegs = 64;
    const vSegs = 64;
    let vertexOffset = 0;

    // Build Left Hemisphere (-1) and Right Hemisphere (+1)
    ([-1, 1] as const).forEach((hemi) => {
      const baseIndex = vertexOffset;

      for (let i = 0; i <= uSegs; i++) {
        const u = i / uSegs;
        for (let j = 0; j <= vSegs; j++) {
          const v = j / vSegs;
          const pos = getAnatomicalSurface(u, v, hemi);

          vertices.push(pos.x, pos.y, pos.z);
          uvs.push(u, v);
          vertexOffset++;
        }
      }

      for (let i = 0; i < uSegs; i++) {
        for (let j = 0; j < vSegs; j++) {
          const a = baseIndex + i * (vSegs + 1) + j;
          const b = baseIndex + (i + 1) * (vSegs + 1) + j;
          const c = baseIndex + (i + 1) * (vSegs + 1) + (j + 1);
          const d = baseIndex + i * (vSegs + 1) + (j + 1);

          indices.push(a, b, d);
          indices.push(b, c, d);
        }
      }
    });

    geo.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    geo.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
    geo.setIndex(indices);
    geo.computeVertexNormals();

    // 2. Generate Neural Mesh Overlay (Points and Axonal Synaptic Lines)
    const neuralPointsArr: number[] = [];
    const neuralColorsArr: number[] = [];
    const linesArr: number[] = [];
    const failureArr: number[] = [];
    const sampledNodes: THREE.Vector3[] = [];

    // Deterministic random
    let seed = 12345;
    function rand() {
      seed = (seed * 16807) % 2147483647;
      return (seed - 1) / 2147483646;
    }

    const posAttr = geo.attributes.position;
    const totalVertices = posAttr.count;

    // Sample ~1200 vertices for the neural mesh nodes
    for (let i = 0; i < totalVertices; i += 7) {
      if (rand() > 0.45) continue;
      const x = posAttr.getX(i);
      const y = posAttr.getY(i);
      const z = posAttr.getZ(i);

      // Elevated slightly above cortex surface
      const normalFactor = 1.025;
      const p = new THREE.Vector3(x * normalFactor, y * normalFactor, z * normalFactor);

      // Categorize: is it in the active failure zone (frontal/temporal cortex)?
      const isFailureZone = (z > 0.3 && y > 0.1 && Math.abs(x) > 0.3) || (y < -0.1 && z > 0.4);

      if (isFailureZone && rand() < 0.22) {
        failureArr.push(p.x, p.y, p.z);
      } else {
        neuralPointsArr.push(p.x, p.y, p.z);
        // Electric cyan with intensity variation
        neuralColorsArr.push(0.0, 0.94, 1.0);
      }

      sampledNodes.push(p);
    }

    // Connect nearest neighbor nodes with glowing synaptic lines
    const maxLineDistSq = 0.045;
    const minLineDistSq = 0.004;
    let connectedLines = 0;
    const maxLines = 1800;

    for (let i = 0; i < sampledNodes.length && connectedLines < maxLines; i += 2) {
      for (let j = i + 1; j < Math.min(i + 35, sampledNodes.length); j++) {
        const d2 = sampledNodes[i].distanceToSquared(sampledNodes[j]);
        if (d2 > minLineDistSq && d2 < maxLineDistSq) {
          linesArr.push(
            sampledNodes[i].x,
            sampledNodes[i].y,
            sampledNodes[i].z,
            sampledNodes[j].x,
            sampledNodes[j].y,
            sampledNodes[j].z
          );
          connectedLines++;
          break;
        }
      }
    }

    // 3. Electrical action potential impulse points
    const impulseCount = 40;
    const impulseCoords = new Float32Array(impulseCount * 3);
    for (let i = 0; i < impulseCount; i++) {
      const node = sampledNodes[Math.floor(rand() * sampledNodes.length)] || new THREE.Vector3();
      impulseCoords[i * 3] = node.x;
      impulseCoords[i * 3 + 1] = node.y;
      impulseCoords[i * 3 + 2] = node.z;
    }

    return {
      cortexGeometry: geo,
      neuralPoints: new Float32Array(neuralPointsArr),
      neuralLines: new Float32Array(linesArr),
      failurePoints: new Float32Array(failureArr),
      impulseData: { coords: impulseCoords, nodes: sampledNodes },
    };
  }, []);

  // Frame animation loop
  useFrame(({ clock }, delta) => {
    if (!mainGroupRef.current) return;

    if (reducedMotion) {
      mainGroupRef.current.rotation.y = 0.65;
      mainGroupRef.current.rotation.x = 0.12;
      mainGroupRef.current.scale.set(1.2, 1.2, 1.2);
      return;
    }

    const t = clock.getElapsedTime();

    // 1. Smooth 360-degree turntable continuous rotation (~24s / rev)
    mainGroupRef.current.rotation.y += delta * 0.26;

    // 2. Gentle organic floating and breathing pulse
    mainGroupRef.current.position.y = Math.sin(t * 0.9) * 0.05;
    const breath = 1.22 + Math.sin(t * 1.6) * 0.015;
    mainGroupRef.current.scale.set(breath, breath, breath);

    // 3. Mouse 3D tilt tracking
    if (mouseX && mouseY) {
      const targetX = (mouseY.current || 0) * 0.22;
      const targetZ = -(mouseX.current || 0) * 0.06;
      mainGroupRef.current.rotation.x += (targetX - mainGroupRef.current.rotation.x) * 0.08;
      mainGroupRef.current.rotation.z += (targetZ - mainGroupRef.current.rotation.z) * 0.08;
    }

    // 4. Moving electrical synaptic pulses along the neural network
    if (impulsePointsRef.current && impulseData.nodes.length > 0) {
      const positions = impulsePointsRef.current.geometry.attributes.position as THREE.BufferAttribute;
      if (positions) {
        const arr = positions.array as Float32Array;
        const total = arr.length / 3;
        for (let i = 0; i < total; i++) {
          const nodeIdx = Math.floor((Math.sin(t * 3.0 + i * 1.5) * 0.5 + 0.5) * (impulseData.nodes.length - 1));
          const node = impulseData.nodes[nodeIdx];
          if (node) {
            arr[i * 3] += (node.x - arr[i * 3]) * 0.12;
            arr[i * 3 + 1] += (node.y - arr[i * 3 + 1]) * 0.12;
            arr[i * 3 + 2] += (node.z - arr[i * 3 + 2]) * 0.12;
          }
        }
        positions.needsUpdate = true;
      }
    }
  });

  return (
    <group ref={mainGroupRef} position={[0, 0, 0]}>
      {/* 1. Translucent Silver Metallic Anatomical Cortex */}
      <mesh ref={cortexMeshRef} geometry={cortexGeometry}>
        <meshPhysicalMaterial
          color="#d1d5db"
          emissive="#05192d"
          emissiveIntensity={0.25}
          roughness={0.22}
          metalness={0.88}
          clearcoat={0.95}
          clearcoatRoughness={0.15}
          transmission={0.35}
          thickness={1.2}
          transparent
          opacity={0.84}
          reflectivity={0.9}
        />
      </mesh>

      {/* 2. Synaptic Neural Mesh Connection Lines */}
      {neuralLines.length > 0 && (
        <lineSegments>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              args={[neuralLines, 3]}
            />
          </bufferGeometry>
          <lineBasicMaterial
            color="#38bdf8"
            transparent
            opacity={0.38}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
          />
        </lineSegments>
      )}

      {/* 3. Glowing Electric Cyan Neural Nodes */}
      <points ref={neuralNodesRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[neuralPoints, 3]}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.065}
          color="#00f0ff"
          transparent
          opacity={0.95}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          map={cyanGlowTexture || undefined}
        />
      </points>

      {/* 4. Active Red Failure Synaptic Nodes (Vulnerability Clusters) */}
      {failurePoints.length > 0 && (
        <points ref={failureNodesRef}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              args={[failurePoints, 3]}
            />
          </bufferGeometry>
          <pointsMaterial
            size={0.11}
            color="#ef4444"
            transparent
            opacity={1.0}
            blending={THREE.AdditiveBlending}
            depthWrite={false}
            map={redGlowTexture || undefined}
          />
        </points>
      )}

      {/* 5. Action Potential Electrical Spark Particles */}
      <points ref={impulsePointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            args={[impulseData.coords, 3]}
          />
        </bufferGeometry>
        <pointsMaterial
          size={0.09}
          color="#ffffff"
          transparent
          opacity={0.9}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          map={cyanGlowTexture || undefined}
        />
      </points>
    </group>
  );
}

export { AnatomicalNeuralBrain as ProceduralBrain };
