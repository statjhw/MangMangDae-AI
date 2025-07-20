// 사용자 정보 타입 (백엔드 API 호출용)
export interface UserInfo {
  candidate_major: string;
  candidate_career: string;
  candidate_interest: string;
  candidate_location: string;
  candidate_tech_stack: string[];
  candidate_question: string;
  candidate_salary: string;
}

// 폼 입력 타입
export interface FormUserInfo {
  education: {
    status: string;
    major: string;
    university?: string;
  };
  career: {
    hasExperience: boolean;
    yearsOfExperience?: number;
    recentJob?: string;
  };
  preferences: {
    desiredJob: string;
    desiredLocation: string;
    desiredSalary: number;
  };
}

// 통계 데이터 타입
export interface Statistics {
  jobPreferences: {
    job: string;
    percentage: number;
  }[];
  salaryDistribution: {
    range: string;
    count: number;
  }[];
  averageSalary: number;
  locationRatio: {
    location: string;
    ratio: number;
  }[];
}

// 채팅 메시지 타입
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// API 응답 타입
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// 직업 분류 타입 (mapping_table.json 기반)
export interface JobCategory {
  id: string;
  name: string;
  category: string;
}

// 워크플로우 응답 타입
export interface WorkflowResponse {
  job_recommendations: string;
  company_info: string;
  salary_info: string;
  preparation_advice: string;
  final_answer: string;
}

// 폼 상태 타입
export interface FormState {
  step: number;
  isComplete: boolean;
  data: Partial<UserInfo>;
} 