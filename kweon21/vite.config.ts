import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    // 현재 디렉토리와 상위 디렉토리에서 .env 파일 로드
    const currentEnv = loadEnv(mode, '.', '');
    const parentEnv = loadEnv(mode, '..', '');
    // 상위 디렉토리의 환경 변수를 우선 사용 (없으면 현재 디렉토리 사용)
    const env = { ...currentEnv, ...parentEnv };
    
    // GEMINI_API_KEY 또는 GOOGLE_API_KEY 중 하나를 사용
    const apiKey = env.GEMINI_API_KEY || env.GOOGLE_API_KEY || process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
    
    return {
      server: {
        port: 3000,
        host: '0.0.0.0',
      },
      plugins: [react()],
      define: {
        'process.env.API_KEY': JSON.stringify(apiKey),
        'process.env.GEMINI_API_KEY': JSON.stringify(apiKey),
        'process.env.GOOGLE_API_KEY': JSON.stringify(apiKey)
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      },
      // 빌드 설정: Flask에서 서빙하기 위한 경로 설정
      build: {
        outDir: 'dist',
        assetsDir: 'assets',
        // 상대 경로로 빌드 (Flask의 /studio 경로에서 서빙)
        base: '/studio/',
        // 소스맵 생성 (개발용)
        sourcemap: false,
        // 청크 크기 경고 비활성화
        chunkSizeWarningLimit: 1000,
      }
    };
});
