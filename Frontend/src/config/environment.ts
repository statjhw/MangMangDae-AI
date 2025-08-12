export const config = {
  apiBaseUrl: import.meta.env.MODE === 'production'
    ? import.meta.env.VITE_API_BASE_URL || 'https://mangmangdae-ai-backend.railway.app'
    : '/api',
  isProd: import.meta.env.MODE === 'production',
  isDev: import.meta.env.MODE === 'development',
  timeout: 180000, // 3 minutes
  // 세션 설정 (메모리 참조)
  sessionTimeout: 3600000, // 1시간 (밀리초)
} as const;

export default config;