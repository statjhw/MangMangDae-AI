import axios from 'axios';
import { UserInfo, Statistics, WorkflowResponse, ApiResponse } from '../types';

const API_BASE_URL = '/api';

// axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000, // 타임아웃을 3분(180,000ms)으로 늘림
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
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
    const response = await api.post('/v1/chat', requestData, {
      withCredentials: true, 
    });

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

export default api; 