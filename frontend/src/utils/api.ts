import axios from 'axios';
import { UserInfo, Statistics, WorkflowResponse, ApiResponse } from '../types';

const API_BASE_URL = '/api';

// axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
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
    console.log('Sending workflow request:', JSON.stringify(userInfo, null, 2));
    
    // 데이터 검증
    console.log('Data validation:');
    console.log('- candidate_major:', userInfo.candidate_major);
    console.log('- candidate_career:', userInfo.candidate_career);
    console.log('- candidate_interest:', userInfo.candidate_interest);
    console.log('- candidate_location:', userInfo.candidate_location);
    console.log('- candidate_tech_stack:', userInfo.candidate_tech_stack);
    console.log('- candidate_question:', userInfo.candidate_question);
    console.log('- candidate_salary:', userInfo.candidate_salary);
    
    const response = await api.post<WorkflowResponse>('/workflow', userInfo);
    console.log('Workflow response:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('Failed to run workflow:', error);
    
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