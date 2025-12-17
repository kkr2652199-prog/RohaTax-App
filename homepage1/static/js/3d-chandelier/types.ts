export interface LightingState {
  intensity: number;
  warmth: number; // 0 to 1 (cool to warm)
  lightColor: string;
}

export interface ChandelierProps {
  lightState: LightingState;
}