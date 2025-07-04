import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useForm } from 'react-hook-form';
import { User, GraduationCap, Briefcase, MapPin, DollarSign } from 'lucide-react';
import Input from '../common/Input';
import Select from '../common/Select';
import Button from '../common/Button';
import { UserInfo } from '../../types';
import { 
  EDUCATION_STATUS_OPTIONS, 
  CAREER_OPTIONS, 
  SALARY_RANGES,
  MAJOR_CITIES 
} from '../../utils/constants';
import { searchJobs, searchUniversities } from '../../utils/api';

interface UserInfoFormProps {
  onSubmit: (data: UserInfo) => void;
  loading?: boolean;
}

const UserInfoForm = ({ onSubmit, loading = false }: UserInfoFormProps) => {
  const [step, setStep] = useState(1);
  const [jobSuggestions, setJobSuggestions] = useState<string[]>([]);
  const [universitySuggestions, setUniversitySuggestions] = useState<string[]>([]);
  
  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<UserInfo>();
  
  const watchedValues = watch();
  const hasExperience = watchedValues.career?.hasExperience;

  // 직업 자동완성
  useEffect(() => {
    const searchJobSuggestions = async () => {
      if (watchedValues.preferences?.desiredJob && watchedValues.preferences.desiredJob.length > 1) {
        try {
          const suggestions = await searchJobs(watchedValues.preferences.desiredJob);
          setJobSuggestions(suggestions);
        } catch (error) {
          console.error('Failed to fetch job suggestions:', error);
        }
      } else {
        setJobSuggestions([]);
      }
    };

    const timeoutId = setTimeout(searchJobSuggestions, 300);
    return () => clearTimeout(timeoutId);
  }, [watchedValues.preferences?.desiredJob]);

  // 대학 자동완성
  useEffect(() => {
    const searchUniversitySuggestions = async () => {
      if (watchedValues.education?.university && watchedValues.education.university.length > 1) {
        try {
          const suggestions = await searchUniversities(watchedValues.education.university);
          setUniversitySuggestions(suggestions);
        } catch (error) {
          console.error('Failed to fetch university suggestions:', error);
        }
      } else {
        setUniversitySuggestions([]);
      }
    };

    const timeoutId = setTimeout(searchUniversitySuggestions, 300);
    return () => clearTimeout(timeoutId);
  }, [watchedValues.education?.university]);

  const handleJobSuggestionSelect = (suggestion: string) => {
    setValue('preferences.desiredJob', suggestion);
    setJobSuggestions([]);
  };

  const handleUniversitySuggestionSelect = (suggestion: string) => {
    setValue('education.university', suggestion);
    setUniversitySuggestions([]);
  };

  const nextStep = () => setStep(step + 1);
  const prevStep = () => setStep(step - 1);

  const steps = [
    {
      title: '학력 정보',
      icon: GraduationCap,
      fields: (
        <div className="space-y-6">
          <Select
            label="학력 상태"
            options={EDUCATION_STATUS_OPTIONS}
            {...register('education.status', { required: '학력 상태를 선택해주세요' })}
            error={errors.education?.status?.message}
          />
          
          <Input
            label="전공"
            placeholder="예: 컴퓨터공학, 경영학, 디자인학"
            {...register('education.major', { required: '전공을 입력해주세요' })}
            error={errors.education?.major?.message}
          />
          
          <Input
            label="대학교 (선택)"
            placeholder="예: 서울대학교, 연세대학교"
            suggestions={universitySuggestions}
            onSuggestionSelect={handleUniversitySuggestionSelect}
            {...register('education.university')}
          />
        </div>
      )
    },
    {
      title: '커리어 정보',
      icon: Briefcase,
      fields: (
        <div className="space-y-6">
          <Select
            label="경력 유무"
            options={CAREER_OPTIONS}
            {...register('career.hasExperience', { required: '경력 유무를 선택해주세요' })}
            error={errors.career?.hasExperience?.message}
          />
          
          {hasExperience && (
            <Input
              label="경력 (년차)"
              type="number"
              placeholder="예: 3"
              min="0"
              max="50"
              {...register('career.yearsOfExperience', { 
                required: hasExperience ? '경력 년차를 입력해주세요' : false,
                min: { value: 0, message: '0년 이상 입력해주세요' },
                max: { value: 50, message: '50년 이하 입력해주세요' }
              })}
              error={errors.career?.yearsOfExperience?.message}
            />
          )}
          
          <Input
            label="최근 직업 (선택)"
            placeholder="예: 프론트엔드 개발자, 마케터"
            suggestions={jobSuggestions}
            onSuggestionSelect={handleJobSuggestionSelect}
            {...register('career.recentJob')}
          />
        </div>
      )
    },
    {
      title: '선호 사항',
      icon: User,
      fields: (
        <div className="space-y-6">
          <Input
            label="희망 직업"
            placeholder="예: 백엔드 개발자, UX 디자이너"
            suggestions={jobSuggestions}
            onSuggestionSelect={handleJobSuggestionSelect}
            {...register('preferences.desiredJob', { required: '희망 직업을 입력해주세요' })}
            error={errors.preferences?.desiredJob?.message}
          />
          
          <Input
            label="희망 위치"
            placeholder="예: 서울특별시, 경기도"
            suggestions={MAJOR_CITIES}
            onSuggestionSelect={(suggestion) => setValue('preferences.desiredLocation', suggestion)}
            {...register('preferences.desiredLocation', { required: '희망 위치를 입력해주세요' })}
            error={errors.preferences?.desiredLocation?.message}
          />
          
          <Select
            label="희망 연봉"
            options={SALARY_RANGES}
            {...register('preferences.desiredSalary', { required: '희망 연봉을 선택해주세요' })}
            error={errors.preferences?.desiredSalary?.message}
          />
        </div>
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
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
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
          ) : (
            <Button
              type="submit"
              loading={loading}
            >
              분석 시작
            </Button>
          )}
        </div>
      </form>
    </motion.div>
  );
};

export default UserInfoForm; 