import axios from 'axios';
import { UserInfo, Statistics, WorkflowResponse, ApiResponse, UserStatResponse, SessionInfo, SessionStats } from '../types';
import { config } from '../config/environment';

const API_BASE_URL = config.apiBaseUrl;

// axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: config.timeout,
  withCredentials: true, // Always include cookies for session management
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터
api.interceptors.request.use(
  (config) => {
    console.log('🚀 API Request:', config.method?.toUpperCase(), config.url);
    // Log session cookie presence
    const sessionCookie = document.cookie.split(';').find(c => c.trim().startsWith('session_id='));
    if (sessionCookie) {
      console.log('🍪 Session cookie present:', sessionCookie.split('=')[1]);
    } else {
      console.log('❌ No session cookie found');
    }
    return config;
  },
  (error) => {
    console.error('❌ Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Session renewal flag to prevent multiple renewal attempts
let isRenewing = false;
let failedQueue: Array<{ resolve: (value?: any) => void; reject: (reason?: any) => void }> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  
  failedQueue = [];
};

// 응답 인터셉터
api.interceptors.response.use(
  (response) => {
    console.log('✅ API Response:', response.status, response.config.url);
    
    // Check for session renewal indicators in response headers
    if (response.headers['x-session-renewed']) {
      console.log('🔄 Session was automatically renewed by backend');
      // Session renewal handled silently in background - no user notification needed
    }
    
    // Check for new session cookie
    const setCookieHeader = response.headers['set-cookie'];
    if (setCookieHeader && setCookieHeader.includes('session_id=')) {
      console.log('🍪 New session cookie set by backend');
    }
    
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // Handle session expiry (401/403) with automatic renewal
    if ((error.response?.status === 401 || error.response?.status === 403) && !originalRequest._retry) {
      console.log('🔑 Session expired (401/403), attempting renewal...');
      
      if (isRenewing) {
        console.log('⏳ Already renewing session, queuing request...');
        // If already renewing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(() => {
          console.log('🔄 Retrying queued request after renewal');
          return api(originalRequest);
        }).catch((err) => {
          console.error('❌ Queued request failed:', err);
          return Promise.reject(err);
        });
      }
      
      originalRequest._retry = true;
      isRenewing = true;
      console.log('🔄 Starting session renewal process...');
      
      try {
        // Attempt session renewal by making a simple request to a different endpoint to avoid loops
        // Use a minimal endpoint that doesn't require session validation
        console.log('🔧 Attempting session renewal via /v1/session/stats...');
        await api.get('/v1/session/stats');
        
        console.log('✅ Session renewal successful!');
        // Session renewed successfully, process queued requests
        processQueue(null, 'renewed');
        
        // Session renewal handled silently - no need to notify user about background session management
        console.log('Session renewed successfully in background');
        
        console.log('🔄 Retrying original request after renewal...');
        // Retry the original request
        return api(originalRequest);
        
      } catch (renewError) {
        console.error('❌ Session renewal failed:', renewError);
        
        // Session renewal failed, process queue with error
        processQueue(renewError, null);
        
        // Only dispatch session expiry event for actual failures that affect user experience
        if (renewError.response?.status !== 401 && renewError.response?.status !== 403) {
          window.dispatchEvent(new CustomEvent('sessionExpired', {
            detail: { message: 'Session management error occurred' }
          }));
        } else {
          console.log('Session could not be renewed, but handled silently');
        }
        
        return Promise.reject(renewError);
      } finally {
        isRenewing = false;
        console.log('🏁 Session renewal process completed');
      }
    }
    
    console.error('API Error:', error.response?.status, error.message);
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

export default api; 