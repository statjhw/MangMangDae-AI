import { Routes, Route } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useEffect } from 'react'
import Header from './components/layout/Header'
import HomePage from './pages/HomePage'
import AboutPage from './pages/AboutPage'
import FeaturesPage from './pages/FeaturesPage'
import { forceNewSession } from './utils/api'
import './App.css'

function App() {
  // 페이지 로드 시 무조건 새 세션 생성
  useEffect(() => {
    // 페이지 새로고침 감지 (Performance API 사용)
    const navigationEntries = performance.getEntriesByType('navigation');
    const navigationType = navigationEntries.length > 0 
      ? (navigationEntries[0] as PerformanceNavigationTiming).type 
      : 'navigate';
      
    console.log('🚀 Navigation type:', navigationType);
    console.log('🔄 Page load detected - forcing complete session reset');
    
    // 1. 먼저 세션 강제 정리
    forceNewSession();
    
    // 2. 추가로 백엔드에 세션 클리어 요청 (비동기, 에러 무시)
    const clearBackendSession = async () => {
      try {
        console.log('🧹 Attempting to clear backend session...');
        const response = await fetch('/api/v1/session/clear', {
          method: 'DELETE',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'X-Force-Clear': 'true'
          }
        });
        if (response.ok) {
          console.log('✅ Backend session cleared successfully');
        } else {
          console.log('⚠️ Backend session clear failed, but continuing...');
        }
      } catch (error) {
        console.log('⚠️ Backend session clear error (ignoring):', error);
      }
    };
    
    // 비동기로 백엔드 세션 정리 시도 (에러가 나도 계속 진행)
    clearBackendSession();
    
    // 3. 페이지를 떠날 때도 세션 정리
    const handleBeforeUnload = () => {
      console.log('📤 Page unloading - marking session for cleanup');
      localStorage.setItem('page_unloaded', Date.now().toString());
      // 쿠키도 다시 한번 정리 시도
      document.cookie = 'session_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
    };
    
    // 4. 페이지 포커스 시에도 세션 상태 확인
    const handlePageFocus = () => {
      console.log('👁️ Page focused - checking session state');
      const lastUnload = localStorage.getItem('page_unloaded');
      if (lastUnload) {
        const unloadTime = parseInt(lastUnload);
        const now = Date.now();
        if (now - unloadTime > 1000) { // 1초 이상 지났으면
          console.log('🔄 Page was unloaded, forcing session reset');
          forceNewSession();
          localStorage.removeItem('page_unloaded');
        }
      }
    };
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('focus', handlePageFocus);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('focus', handlePageFocus);
    };
  }, []);
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Header />
      <AnimatePresence mode="wait">
        <Routes>
          <Route 
            path="/" 
            element={
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.5 }}
              >
                <HomePage />
              </motion.div>
            } 
          />
          <Route 
            path="/about" 
            element={
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.5 }}
              >
                <AboutPage />
              </motion.div>
            } 
          />
          <Route 
            path="/features" 
            element={
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.5 }}
              >
                <FeaturesPage />
              </motion.div>
            } 
          />
        </Routes>
      </AnimatePresence>
    </div>
  )
}

export default App 