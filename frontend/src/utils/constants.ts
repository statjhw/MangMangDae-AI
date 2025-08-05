// 학력 상태 옵션
export const EDUCATION_STATUS_OPTIONS = [
  { value: 'university_student', label: '대학교 재학' },
  { value: 'university_graduate', label: '대학교 졸업' },
  { value: 'graduate_student', label: '대학원 재학' },
  { value: 'graduate_graduate', label: '대학원 졸업' },
  { value: 'high_school_graduate', label: '고등학교 졸업' },
];

// 경력 유무 옵션
export const CAREER_OPTIONS = [
  { value: 'newcomer', label: '신입' },
  { value: 'experienced', label: '경력' },
];

// 연봉 범위 옵션 (단위: 만원)
export const SALARY_RANGES = [
  { value: '2000만원 이하', label: '2000만원 이하' },
  { value: '2000-2500만원', label: '2000-2500만원' },
  { value: '2500-3000만원', label: '2500-3000만원' },
  { value: '3000-3500만원', label: '3000-3500만원' },
  { value: '3500-4000만원', label: '3500-4000만원' },
  { value: '4000-4500만원', label: '4000-4500만원' },
  { value: '4500-5000만원', label: '4500-5000만원' },
  { value: '5000-6000만원', label: '5000-6000만원' },
  { value: '6000-7000만원', label: '6000-7000만원' },
  { value: '7000만원 이상', label: '7000만원 이상' },
];

// 주요 도시 목록
export const MAJOR_CITIES = [
  '서울특별시',
  '부산광역시',
  '대구광역시',
  '인천광역시',
  '광주광역시',
  '대전광역시',
  '울산광역시',
  '세종특별자치시',
  '경기도',
  '강원도',
  '충청북도',
  '충청남도',
  '전라북도',
  '전라남도',
  '경상북도',
  '경상남도',
  '제주특별자치도',
];

// 애니메이션 설정
export const ANIMATION_CONFIG = {
  duration: 0.5,
  ease: [0.4, 0, 0.2, 1],
};

// API 설정
export const API_CONFIG = {
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
};

// 차트 색상 팔레트
export const CHART_COLORS = [
  '#3B82F6', // blue-500
  '#10B981', // emerald-500
  '#F59E0B', // amber-500
  '#EF4444', // red-500
  '#8B5CF6', // violet-500
  '#06B6D4', // cyan-500
  '#84CC16', // lime-500
  '#F97316', // orange-500
];

// 로컬 스토리지 키
export const STORAGE_KEYS = {
  USER_INFO: 'mmd_user_info',
  CHAT_HISTORY: 'mmd_chat_history',
  FORM_STATE: 'mmd_form_state',
}; 