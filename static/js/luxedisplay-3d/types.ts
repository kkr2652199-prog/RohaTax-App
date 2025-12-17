export interface BoxConfig {
  id: number;
  position: [number, number, number];
  color: string;
}

export interface ChatMessage {
  role: 'user' | 'model';
  text: string;
  isLoading?: boolean;
}

export interface ShowcaseProps {
  boxCount: number;
  showcaseLength: number;
}
