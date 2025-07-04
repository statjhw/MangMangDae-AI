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
export const runWorkflow = async (userInfo: UserInfo, question: string): Promise<WorkflowResponse> => {
  try {
    const response = await api.post<ApiResponse<WorkflowResponse>>('/workflow', {
      candidate_major: userInfo.education.major,
      candidate_career: userInfo.career.hasExperience ? `${userInfo.career.yearsOfExperience}년` : '신입',
      candidate_interest: userInfo.preferences.desiredJob,
      candidate_question: question,
    });
    return response.data.data!;
  } catch (error) {
    console.error('Failed to run workflow:', error);
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