import axios from 'axios';
import { UserInfo, Statistics, WorkflowResponse, ApiResponse, UserStatResponse, SessionInfo, SessionStats } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000, // 타임아웃을 3분(180,000ms)으로 늘림
  withCredentials: true, // Always include cookies for session management
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터
api.interceptors.request.use(
  (config) => {
    console.log('🚀 API Request:', config.method?.toUpperCase(), config.url);
    
    // 페이지 로드 후 첫 번째 요청인 경우 특별 헤더 추가
    if (isPageLoad) {
      config.headers['X-Page-Load'] = 'true';
      config.headers['X-Page-Load-Timestamp'] = Date.now().toString();
      config.headers['X-Force-New-Session'] = 'true';
      console.log('🔄 First request after page load - added session reset headers');
      console.log('📤 Headers added:', {
        'X-Page-Load': 'true',
        'X-Page-Load-Timestamp': config.headers['X-Page-Load-Timestamp'],
        'X-Force-New-Session': 'true'
      });
      isPageLoad = false; // 첫 번째 요청 후 플래그 해제
    }
    
    // 전체 쿠키 상태 로깅
    console.log('🍪 All cookies:', document.cookie);
    
    // 세션 쿠키 확인
    const sessionCookie = document.cookie.split(';').find(c => c.trim().startsWith('session_id='));
    if (sessionCookie) {
      const sessionId = sessionCookie.split('=')[1];
      console.log('🍪 Session cookie present:', sessionId.substring(0, 8) + '...');
    } else {
      console.log('❌ No session cookie found - backend will create new session');
    }
    
    // 요청 헤더 전체 로깅 (디버깅용)
    console.log('📋 Request headers:', {
      'X-Page-Load': config.headers['X-Page-Load'],
      'X-Force-New-Session': config.headers['X-Force-New-Session'],
      'Content-Type': config.headers['Content-Type'],
      'User-Agent': navigator.userAgent.substring(0, 50) + '...'
    });
    
    return config;
  },
  (error) => {
    console.error('❌ Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// 단순화된 에러 처리 - 복잡한 갱신 로직 제거

// 페이지 로드 시 기대하는 세션 ID 저장
let expectedNewSessionAfterPageLoad = false;
let lastKnownSessionId: string | null = null;

// 단순화된 응답 인터셉터
api.interceptors.response.use(
  (response) => {
    console.log('✅ API Response:', response.status, response.config.url);
    
    // 세션 리셋 헤더 확인
    const sessionReset = response.headers['x-session-reset'];
    const newSessionId = response.headers['x-new-session-id'];
    
    if (sessionReset === 'true') {
      console.log('🔄 Backend confirmed session reset');
      expectedNewSessionAfterPageLoad = false;
      lastKnownSessionId = null;
    }
    
    // 채팅 응답에서 세션 ID 확인
    if (response.config.url?.includes('/v1/chat') && response.data?.session_id) {
      const responseSessionId = response.data.session_id;
      
      if (expectedNewSessionAfterPageLoad && lastKnownSessionId && responseSessionId === lastKnownSessionId) {
        console.warn('⚠️ WARNING: Expected new session but got same ID:', responseSessionId);
        console.warn('🔄 Forcing manual session invalidation...');
        
        // 강제로 세션 무효화
        forceNewSession();
        
        // 백엔드에도 강제 리셋 요청
        fetch('/api/v1/session/clear', {
          method: 'DELETE',
          credentials: 'include',
          headers: { 'X-Force-Clear': 'true' }
        }).catch(e => console.log('Failed to force clear:', e));
        
        return Promise.reject(new Error('Session was not properly reset. Please try again.'));
      }
      
      lastKnownSessionId = responseSessionId;
      expectedNewSessionAfterPageLoad = false;
    }
    
    return response;
  },
  (error) => {
    console.error('❌ API Error:', error.response?.status, error.message);
    
    // 401/403 에러 시 단순하게 에러만 반환 (복잡한 갱신 로직 제거)
    if (error.response?.status === 401 || error.response?.status === 403) {
      console.log('🔑 Session expired - user will need to refresh page');
    }
    
    return Promise.reject(error);
  }
);

// 통계 데이터 조회
export const getStatistics = async (userInfo: UserInfo): Promise<Statistics> => {
  try {
    const response = await api.post<ApiResponse<Statistics>>('/statistics', userInfo);
    return response.data.data!;
  } catch (error) {
    console.error('Failed to fetch statistics:', error);
    throw error;
  }
};

// 사용자 맞춤 통계 조회
export const getUserStat = async (userInfo: UserInfo): Promise<UserStatResponse> => {
  try {
    // 사용자 정보를 직접 POST로 전송해서 통계 생성
    const requestData = {
      user_profile: {
        candidate_major: userInfo.candidate_major,
        candidate_career: userInfo.candidate_career,
        candidate_interest: userInfo.candidate_interest,
        candidate_location: userInfo.candidate_location,
        candidate_tech_stack: userInfo.candidate_tech_stack,
        candidate_salary: userInfo.candidate_salary,
      }
    };

    const response = await api.post<UserStatResponse>('/v1/user_stat', requestData);
    
    console.log('User stat response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch user statistics:', error);
    throw error;
  }
};

// 워크플로우 실행
export const runWorkflow = async (userInfo: UserInfo): Promise<WorkflowResponse> => {
  try {
    // 1. 새로운 API 형식에 맞게 요청 데이터를 재구성합니다.
    const requestData = {
      question: userInfo.candidate_question,
      user_profile: {
        candidate_major: userInfo.candidate_major,
        candidate_career: userInfo.candidate_career,
        candidate_interest: userInfo.candidate_interest,
        candidate_location: userInfo.candidate_location,
        candidate_tech_stack: userInfo.candidate_tech_stack,
        candidate_salary: userInfo.candidate_salary,
      }
    };

    console.log('Sending chat request:', JSON.stringify(requestData, null, 2));

    // 2. 새로운 엔드포인트로 요청을 보내고, 세션을 위해 쿠키를 함께 전송합니다.
    const response = await api.post('/v1/chat', requestData);

    console.log('Chat response:', response.data);
    
    // 3. 백엔드 응답(answer, session_id)을 기존 프론트엔드 타입(WorkflowResponse)에 맞게 변환합니다.
    const result: WorkflowResponse = {
      session_id: response.data.session_id,
      final_answer: response.data.answer,
    };
    return result;

  } catch (error: any) {
    console.error('Failed to run chat workflow:', error);
    
    // 422 에러의 경우 상세 정보 출력
    if (error.response?.status === 422) {
      console.error('Validation error details:', error.response.data);
      if (error.response.data?.detail) {
        console.error('Detailed validation errors:');
        error.response.data.detail.forEach((err: any, index: number) => {
          console.error(`${index + 1}. Field: ${err.loc?.join('.')} | Error: ${err.msg} | Input: ${err.input}`);
        });
      }
    }
    
    throw error;
  }
};

// 직업 자동완성 검색
export const searchJobs = async (query: string): Promise<string[]> => {
  try {
    const response = await api.get<ApiResponse<string[]>>(`/jobs/search?q=${encodeURIComponent(query)}`);
    return response.data.data || [];
  } catch (error) {
    console.error('Failed to search jobs:', error);
    return [];
  }
};

// 대학 자동완성 검색
export const searchUniversities = async (query: string): Promise<string[]> => {
  try {
    const response = await api.get<ApiResponse<string[]>>(`/universities/search?q=${encodeURIComponent(query)}`);
    return response.data.data || [];
  } catch (error) {
    console.error('Failed to search universities:', error);
    return [];
  }
};

// Session management endpoints
export const resetConversation = async (): Promise<ApiResponse<{ message: string }>> => {
  try {
    const response = await api.post<ApiResponse<{ message: string }>>('/v1/chat/reset', {});
    return response.data;
  } catch (error) {
    console.error('Failed to reset conversation:', error);
    throw error;
  }
};

export const getSessionInfo = async (): Promise<SessionInfo> => {
  try {
    const response = await api.get<SessionInfo>('/v1/session/info');
    return response.data;
  } catch (error) {
    console.error('Failed to get session info:', error);
    throw error;
  }
};

export const getSessionStats = async (): Promise<SessionStats> => {
  try {
    const response = await api.get<SessionStats>('/v1/session/stats');
    return response.data;
  } catch (error) {
    console.error('Failed to get session stats:', error);
    throw error;
  }
};

export const clearSession = async (): Promise<ApiResponse<{ message: string }>> => {
  try {
    const response = await api.delete<ApiResponse<{ message: string }>>('/v1/session/clear');
    return response.data;
  } catch (error) {
    console.error('Failed to clear session:', error);
    throw error;
  }
};

// 페이지 로드 플래그 (새로고침 감지용)
let isPageLoad = true;

// 새로고침 시 완전히 새로운 세션 생성
export const forceNewSession = (): void => {
  try {
    console.log('🔄 Forcing new session on page load...');
    isPageLoad = true; // 페이지 로드 플래그 설정
    expectedNewSessionAfterPageLoad = true; // 새 세션 기대 플래그 설정
    
    // 현재 쿠키 상태 로깅
    console.log('🍪 Current cookies before deletion:', document.cookie);
    
    // 더 강력한 쿠키 삭제 전략
    const cookiesToDelete = ['session_id'];
    const hostname = window.location.hostname;
    const port = window.location.port;
    const protocol = window.location.protocol;
    
    console.log(`🌐 Current location: ${protocol}//${hostname}${port ? ':' + port : ''}`);
    
    cookiesToDelete.forEach(cookieName => {
      // 현재 쿠키 값 확인
      const currentValue = document.cookie.split(';').find(c => c.trim().startsWith(`${cookieName}=`));
      console.log(`🔍 Current ${cookieName} cookie:`, currentValue);
      
      // 더 포괄적인 삭제 시도
      const deletionAttempts = [
        // 기본 삭제
        `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`,
        `${cookieName}=; Max-Age=0; path=/;`,
        
        // 현재 도메인 관련
        `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=${hostname};`,
        `${cookieName}=; Max-Age=0; path=/; domain=${hostname};`,
        
        // 점 도메인 (subdomain 포함)
        `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=.${hostname};`,
        `${cookieName}=; Max-Age=0; path=/; domain=.${hostname};`,
        
        // API path 관련
        `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/api;`,
        `${cookieName}=; Max-Age=0; path=/api;`,
        `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/api; domain=${hostname};`,
        
        // localhost 특별 처리
        ...(hostname === 'localhost' ? [
          `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=localhost;`,
          `${cookieName}=; Max-Age=0; path=/; domain=localhost;`,
          `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`,
          `${cookieName}=; Max-Age=0; path=/;`
        ] : []),
        
        // 127.0.0.1 특별 처리
        ...(hostname === '127.0.0.1' ? [
          `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=127.0.0.1;`,
          `${cookieName}=; Max-Age=0; path=/; domain=127.0.0.1;`
        ] : [])
      ];
      
      deletionAttempts.forEach((attempt, index) => {
        document.cookie = attempt;
        console.log(`🗑️ Cookie deletion attempt ${index + 1}:`, attempt);
      });
      
      // 삭제 후 즉시 확인
      setTimeout(() => {
        const afterValue = document.cookie.split(';').find(c => c.trim().startsWith(`${cookieName}=`));
        console.log(`🔍 ${cookieName} after deletion:`, afterValue || 'DELETED');
      }, 50);
    });
    
    // 로컬 스토리지와 세션 스토리지도 정리
    localStorage.removeItem('session_id');
    sessionStorage.removeItem('session_id');
    localStorage.removeItem('page_unloaded');
    
    // 브라우저 캐시도 강제로 무효화
    if ('caches' in window) {
      caches.keys().then(cacheNames => {
        cacheNames.forEach(cacheName => {
          console.log('🗑️ Clearing cache:', cacheName);
          caches.delete(cacheName);
        });
      });
    }
    
    // 최종 상태 확인
    setTimeout(() => {
      console.log('🍪 Final cookies state:', document.cookie);
      console.log('💾 localStorage session_id:', localStorage.getItem('session_id'));
      console.log('📦 sessionStorage session_id:', sessionStorage.getItem('session_id'));
      console.log('✅ Complete session cleanup finished');
    }, 200);
    
  } catch (error) {
    console.error('❌ Failed to clear session data:', error);
  }
};

// 개발자 도구용 디버깅 함수들 (전역 window 객체에 추가)
if (typeof window !== 'undefined') {
  (window as any).debugSession = {
    // 현재 세션 상태 확인
    checkSession: () => {
      console.log('=== 세션 디버깅 정보 ===');
      console.log('🍪 현재 쿠키:', document.cookie);
      console.log('💾 로컬스토리지:', localStorage.getItem('session_id'));
      console.log('📦 세션스토리지:', sessionStorage.getItem('session_id'));
      console.log('🔄 페이지로드 플래그:', isPageLoad);
    },
    
    // 강제로 새 세션 생성
    forceNew: () => {
      console.log('🔄 개발자 도구에서 새 세션 강제 생성...');
      forceNewSession();
    },
    
    // 다음 요청에서 새 세션이 생성되도록 설정
    markPageLoad: () => {
      isPageLoad = true;
      console.log('🏁 다음 API 요청에서 X-Page-Load 헤더 전송됨');
    }
  };
  
  console.log('🛠️ 세션 디버깅 함수 사용법:');
  console.log('  - debugSession.checkSession(): 현재 세션 상태 확인');
  console.log('  - debugSession.forceNew(): 새 세션 강제 생성');
  console.log('  - debugSession.markPageLoad(): 다음 요청을 페이지 로드로 표시');
}

export default api; 