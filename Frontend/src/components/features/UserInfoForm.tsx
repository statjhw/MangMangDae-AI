import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useForm, Controller } from 'react-hook-form';
import { User, GraduationCap, Briefcase, MapPin, Settings, MessageSquare, Sparkles, Code, Zap, ArrowRight } from 'lucide-react';
import Input from '../common/Input';
import Select from '../common/Select';
import Textarea from '../common/Textarea';
import Button from '../common/Button';
import { 
  EDUCATION_STATUS_OPTIONS, 
  SALARY_RANGES,
  MAJOR_CITIES 
} from '../../utils/constants';
import { UserInfo } from '../../types';
import jobCategories from '../../../mapping.json';
import jobSubCategories from '../../../mapping_table.json';

interface UserInfoFormProps {
  onSubmit: (data: UserInfo) => void;
  loading?: boolean;
}

interface FormData {
  education: {
    status: string;
    major: string;
    university: string;
  };
  career: {
    hasExperience: string;
    recentJob: string;
  };
  preferences: {
    jobCategory: string;
    desiredJob: string;
    desiredLocation: string;
    desiredSalary: string;
  };
  additional: {
    techStack: string;
    question: string;
  };
}

const UserInfoForm = ({ onSubmit, loading = false }: UserInfoFormProps) => {
  const [step, setStep] = useState(1);
  const [availableJobs, setAvailableJobs] = useState<Array<{value: string, label: string}>>([]);
  
  const { register, handleSubmit, watch, setValue, control, formState: { errors } } = useForm<FormData>();
  
  const watchedValues = watch();
  const hasExperience = watchedValues.career?.hasExperience === '경력';
  const selectedJobCategory = watchedValues.preferences?.jobCategory;

  // 직군 선택시 직무 목록 업데이트
  useEffect(() => {
    if (selectedJobCategory && jobSubCategories[selectedJobCategory]) {
      const jobs = Object.entries(jobSubCategories[selectedJobCategory]).map(([value, label]) => ({
        value: label as string,
        label: label as string
      }));
      setAvailableJobs(jobs);
      setValue('preferences.desiredJob', ''); // 직무 선택 초기화
    } else {
      setAvailableJobs([]);
      setValue('preferences.desiredJob', ''); // 직무 선택 초기화
    }
  }, [selectedJobCategory, setValue]);

  const nextStep = () => setStep(step + 1);
  const prevStep = () => setStep(step - 1);

  const handleFormSubmit = (data: FormData) => {
    // user_input 형식으로 데이터 변환
    const user_input = {
      candidate_major: `대학교: ${data.education.university || '미기재'}, 전공: ${data.education.major}, 상태: ${data.education.status}`,
      candidate_career: `${data.career.hasExperience}${data.career.recentJob ? `, 최근 직업: ${data.career.recentJob}` : ''}`,
      candidate_interest: data.preferences.desiredJob,
      candidate_location: data.preferences.desiredLocation,
      candidate_tech_stack: data.additional.techStack ? data.additional.techStack.split(',').map(s => s.trim()) : [],
      candidate_question: data.additional.question,
      candidate_salary: data.preferences.desiredSalary
    };
    
    onSubmit(user_input);
  };

  const jobCategoryOptions = Object.entries(jobCategories).map(([value, label]) => ({
    value,
    label
  }));

  const steps = [
    {
      title: '학력 정보',
      icon: GraduationCap,
      fields: (
        <div className="space-y-6">
          <Controller
            name="education.status"
            control={control}
            defaultValue=""
            rules={{ required: '학력 상태를 선택해주세요' }}
            render={({ field }) => (
              <Select
                label="학력 상태"
                options={EDUCATION_STATUS_OPTIONS}
                value={field.value || ''}
                onChange={field.onChange}
                error={errors.education?.status?.message}
              />
            )}
          />
          
          <Controller
            name="education.major"
            control={control}
            defaultValue=""
            rules={{ required: '전공을 입력해주세요' }}
            render={({ field }) => (
              <Input
                label="전공"
                placeholder="예: 컴퓨터공학, 경영학, 디자인학"
                value={field.value || ''}
                onChange={field.onChange}
                error={errors.education?.major?.message}
              />
            )}
          />
          
          <Controller
            name="education.university"
            control={control}
            defaultValue=""
            render={({ field }) => (
              <Input
                label="대학교 (선택)"
                placeholder="예: 서울대학교, 연세대학교"
                value={field.value || ''}
                onChange={field.onChange}
              />
            )}
          />
        </div>
      )
    },
    {
      title: '커리어 정보',
      icon: Briefcase,
      fields: (
        <div className="space-y-6">
          <Controller
            name="career.hasExperience"
            control={control}
            defaultValue=""
            rules={{ required: '경력 구분을 선택해주세요' }}
            render={({ field }) => (
              <Select
                label="경력 구분"
                options={[
                  { value: '경력', label: '경력' },
                  { value: '신입', label: '신입' }
                ]}
                value={field.value || ''}
                onChange={field.onChange}
                error={errors.career?.hasExperience?.message}
              />
            )}
          />
          
          {hasExperience && (
            <Controller
              name="career.recentJob"
              control={control}
              defaultValue=""
              rules={{ required: hasExperience ? '최근 직업을 입력해주세요' : false }}
              render={({ field }) => (
                <Input
                  label="최근 직업"
                  placeholder="예: 프론트엔드 개발자, 마케터"
                  value={field.value || ''}
                  onChange={field.onChange}
                  error={errors.career?.recentJob?.message}
                />
              )}
            />
          )}
        </div>
      )
    },
    {
      title: '선호 직업',
      icon: User,
      fields: (
        <div className="space-y-6">
          <Controller
            name="preferences.jobCategory"
            control={control}
            defaultValue=""
            rules={{ required: '희망 직군을 선택해주세요' }}
            render={({ field }) => (
              <Select
                label="희망 직군"
                options={jobCategoryOptions}
                value={field.value || ''}
                onChange={field.onChange}
                error={errors.preferences?.jobCategory?.message}
              />
            )}
          />
          
          <Controller
            name="preferences.desiredJob"
            control={control}
            defaultValue=""
            rules={{ required: '희망 직무를 선택해주세요' }}
            render={({ field }) => (
              <Select
                label="희망 직무"
                options={availableJobs}
                value={field.value || ''}
                onChange={field.onChange}
                error={errors.preferences?.desiredJob?.message}
                disabled={!selectedJobCategory}
              />
            )}
          />
          
          <Controller
            name="preferences.desiredLocation"
            control={control}
            defaultValue=""
            rules={{ required: '희망 위치를 입력해주세요' }}
            render={({ field }) => (
              <Input
                label="희망 위치"
                placeholder="예: 서울특별시, 경기도"
                suggestions={MAJOR_CITIES}
                onSuggestionSelect={(suggestion) => {
                  const mockEvent = {
                    target: { value: suggestion }
                  } as React.ChangeEvent<HTMLInputElement>;
                  field.onChange(mockEvent);
                }}
                value={field.value || ''}
                onChange={field.onChange}
                error={errors.preferences?.desiredLocation?.message}
              />
            )}
          />
          
          <Controller
            name="preferences.desiredSalary"
            control={control}
            defaultValue=""
            rules={{ required: '희망 연봉을 선택해주세요' }}
            render={({ field }) => (
              <Select
                label="희망 연봉"
                options={SALARY_RANGES}
                value={field.value || ''}
                onChange={field.onChange}
                error={errors.preferences?.desiredSalary?.message}
              />
            )}
          />
        </div>
      )
    },
    {
      title: '기술 스택 & 자격증',
      icon: Code,
      fields: (
        <motion.div
          className="relative"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-2xl p-6 border border-emerald-100 shadow-lg">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-r from-emerald-600 to-teal-600 rounded-full shadow-lg">
                <Code className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-secondary-800 flex items-center gap-2">
                  보유 기술 스택 & 자격증
                  <Zap className="w-5 h-5 text-emerald-600" />
                </h3>
                <p className="text-sm text-secondary-600 mt-1">
                  보유하고 있는 기술, 자격증, 도구 등을 모두 입력해주세요
                </p>
              </div>
            </div>
            
            <Controller
              name="additional.techStack"
              control={control}
              defaultValue=""
              rules={{ required: false }}
              render={({ field }) => (
                <div className="relative">
                  <motion.textarea
                    ref={field.ref}
                    className="w-full px-4 py-4 border-2 border-emerald-200 rounded-xl bg-white/70 backdrop-blur-sm transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 placeholder-secondary-400 resize-none text-base leading-relaxed min-h-[120px] shadow-sm"
                    placeholder="💼 예시: Python, React, TypeScript, AWS, Docker, Git, PostgreSQL, 정보처리기사, AWS Solutions Architect, PMP, SQLD, 토익 850점, Photoshop, Figma, 데이터분석 준전문가(ADsP)"
                    value={field.value || ''}
                    onChange={field.onChange}
                    whileFocus={{ scale: 1.02 }}
                    transition={{ duration: 0.2 }}
                  />
                  {errors.additional?.techStack && (
                    <motion.p
                      className="mt-2 text-sm text-red-600 flex items-center gap-1"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                    >
                      <span className="text-red-500">⚠️</span>
                      {errors.additional?.techStack?.message}
                    </motion.p>
                  )}
                </div>
              )}
            />
            
            <div className="mt-4 space-y-3">
              <div className="flex items-center gap-2 text-sm text-secondary-600">
                <span className="flex items-center gap-1">
                  <span className="text-emerald-600">💡</span>
                  팁: 쉼표로 구분하여 입력하세요 (기술, 자격증, 점수 등 모두 포함)
                </span>
              </div>
              
              {/* 간단한 추천 버튼들 */}
              <div className="flex flex-wrap gap-2">
                {[
                  'Python', 'JavaScript', 'React', 'Java', 'AWS', 'Docker', 'MySQL', 'Git',
                  'Figma', 'Photoshop', '정보처리기사', 'SQLD', '토익', 'OPIC', 'AWS Solutions Architect'
                ].map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => {
                      const currentValue = watchedValues.additional?.techStack || '';
                      const newValue = currentValue ? `${currentValue}, ${item}` : item;
                      setValue('additional.techStack', newValue);
                    }}
                    className="px-3 py-1.5 bg-white/80 hover:bg-emerald-100 border border-emerald-200 rounded-full text-sm text-emerald-700 transition-colors duration-200 shadow-sm hover:shadow-md"
                  >
                    + {item}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      )
    },
    {
      title: 'AI 컨설팅',
      icon: MessageSquare,
      fields: (
        <motion.div
          className="relative"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <div className="bg-gradient-to-br from-primary-50 to-blue-50 rounded-2xl p-6 border border-primary-100 shadow-lg">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-r from-primary-600 to-blue-600 rounded-full shadow-lg">
                <MessageSquare className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-secondary-800 flex items-center gap-2">
                  AI 컨설턴트에게 질문하기
                  <Sparkles className="w-5 h-5 text-primary-600" />
                </h3>
                <p className="text-sm text-secondary-600 mt-1">
                  개인 맞춤형 커리어 조언을 받아보세요
                </p>
              </div>
            </div>
            
            <Controller
              name="additional.question"
              control={control}
              defaultValue=""
              rules={{ 
                required: '상세 질문을 입력해주세요',
                minLength: {
                  value: 25,
                  message: '질문은 최소 25자 이상 입력해주세요'
                },
                maxLength: {
                  value: 500,
                  message: '질문은 최대 500자까지 입력 가능합니다'
                }
              }}
              render={({ field }) => (
                <div className="relative">
                  <motion.textarea
                    ref={field.ref}
                    className="w-full px-4 py-4 border-2 border-primary-200 rounded-xl bg-white/70 backdrop-blur-sm transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 placeholder-secondary-400 resize-none text-base leading-relaxed min-h-[140px] shadow-sm"
                    placeholder="💭 예시: AI 분야로 커리어를 전환하고 싶은데, 어떤 준비를 해야 할까요? 현재 제 경험을 어떻게 활용할 수 있을까요? (최소 25자, 최대 500자)"
                    value={field.value || ''}
                    onChange={field.onChange}
                    whileFocus={{ scale: 1.02 }}
                    transition={{ duration: 0.2 }}
                  />
                  
                  {/* 글자 수 카운터 */}
                  <div className="absolute bottom-3 right-3 text-xs text-secondary-500 bg-white/80 px-2 py-1 rounded-full">
                    {(field.value || '').length}/500
                    {(field.value || '').length < 25 && (
                      <span className="text-red-500 ml-1">(최소 25자)</span>
                    )}
                  </div>
                  {errors.additional?.question && (
                    <motion.p
                      className="mt-2 text-sm text-red-600 flex items-center gap-1"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                    >
                      <span className="text-red-500">⚠️</span>
                      {errors.additional?.question?.message}
                    </motion.p>
                  )}
                </div>
              )}
            />
            
            <div className="mt-4 flex items-center gap-2 text-sm text-secondary-600">
              <span className="flex items-center gap-1">
                <span className="text-primary-600">💡</span>
                팁: 구체적인 상황과 목표를 포함하면 더 정확한 조언을 받을 수 있어요
              </span>
            </div>
          </div>
        </motion.div>
      )
    }
  ];

  const currentStep = steps[step - 1];

  return (
    <motion.div
      className="max-w-2xl mx-auto"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      {/* 진행 단계 표시 */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          {steps.map((s, index) => (
            <div key={index} className="flex items-center">
              <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors ${
                step > index + 1 
                  ? 'bg-primary-600 border-primary-600 text-white' 
                  : step === index + 1
                  ? 'border-primary-600 text-primary-600'
                  : 'border-secondary-300 text-secondary-400'
              }`}>
                {step > index + 1 ? (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ duration: 0.3 }}
                  >
                    ✓
                  </motion.div>
                ) : (
                  <s.icon className="w-5 h-5" />
                )}
              </div>
              {index < steps.length - 1 && (
                <div className={`w-16 h-0.5 mx-2 ${
                  step > index + 1 ? 'bg-primary-600' : 'bg-secondary-300'
                }`} />
              )}
            </div>
          ))}
        </div>
        <h2 className="text-2xl font-bold text-secondary-800 text-center">
          {currentStep.title}
        </h2>
      </div>

      {/* 폼 필드 */}
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            {currentStep.fields}
          </motion.div>
        </AnimatePresence>

        {/* 네비게이션 버튼 */}
        <div className="flex justify-between pt-6">
          <Button
            type="button"
            variant="outline"
            onClick={prevStep}
            disabled={step === 1}
          >
            이전
          </Button>
          
          {step < steps.length ? (
            <Button
              type="button"
              onClick={nextStep}
            >
              다음
            </Button>
          ) : null}
        </div>
        
        {/* 질문 입력 후 가운데 분석 시작 버튼 */}
        {step === steps.length && watchedValues.additional?.question && (
          <motion.div
            className="text-center mt-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Button
              type="submit"
              loading={loading}
              size="lg"
              className="inline-flex items-center space-x-2 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white"
            >
              <span>분석 시작하기</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </motion.div>
        )}
      </form>
    </motion.div>
  );
};

export default UserInfoForm; 