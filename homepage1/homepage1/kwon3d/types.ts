export interface Position {
  x: number;
  y: number;
  z: number;
}

export interface ViewerProps {
  autoRotate: boolean;
  showConfetti: boolean;
}

export enum AnimationState {
  IDLE = 'IDLE',
  HOVER = 'HOVER',
}