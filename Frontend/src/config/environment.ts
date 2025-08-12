export const config = {
  apiBaseUrl: import.meta.env.PROD 
    ? 'https://mangmangdae-ai-backend.railway.app/api'
    : '/api',
  isProd: import.meta.env.PROD,
  isDev: import.meta.env.DEV,
  timeout: 180000, // 3 minutes
} as const;

export default config;