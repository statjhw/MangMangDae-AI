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

// 채팅 메시지 타입
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
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
  session_id?: string; // session_id를 선택적 필드로 추가
  job_recommendations?: string;
  company_info?: string;
  salary_info?: string;
  preparation_advice?: string;
  final_answer: string;
}

// 폼 상태 타입
export interface FormState {
  step: number;
  isComplete: boolean;
  data: Partial<UserInfo>;
}

// 사용자 통계 응답 타입 (백엔드 API 응답)
export interface UserStatResponse {
  user_info: {
    전공: string;
    경력: string;
    관심분야: string;
    희망지역: string;
    기술스택: string;
  };
  interest: {
    interest: string;
    total_job: number;
  };
  tech_stack: {
    [techName: string]: number;
  };
}

// 세션 정보 타입
export interface SessionInfo {
  session_id: string;
  created_at: string;
  last_activity: string;
  expires_at: string;
  message_count: number;
  is_active: boolean;
  time_until_expiry: number; // seconds until expiry
}

// 세션 통계 타입
export interface SessionStats {
  total_sessions: number;
  active_sessions: number;
  total_messages: number;
  avg_session_duration: number;
  most_recent_activity: string;
}

// 세션 상태 타입
export type SessionStatus = 'active' | 'expired' | 'renewed' | 'reset';

// 컨텍스트 리셋 이유 타입
export type ResetReason = 'manual' | 'message_limit' | 'topic_shift' | 'reset_phrase' | 'session_renewal';

// 컨텍스트 리셋 이벤트 타입
export interface ContextResetEvent {
  reason: ResetReason;
  timestamp: Date;
  message?: string;
}