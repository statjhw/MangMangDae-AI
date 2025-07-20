import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, User, Loader2, MessageCircle, Sparkles, CheckCircle, Clock } from 'lucide-react';
import { UserInfo } from '../../types';
import { runWorkflow } from '../../utils/api';
import toast from 'react-hot-toast';

interface ResponseSectionProps {
  userInfo: UserInfo;
}

const ResponseSection = ({ userInfo }: ResponseSectionProps) => {
  const [response, setResponse] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [startTime, setStartTime] = useState<Date | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);

  // 타이머 효과
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isLoading && startTime) {
      interval = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime.getTime()) / 1000));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isLoading, startTime]);

  // 초기 로드 시 API 호출
  useEffect(() => {
    if (isInitialLoad && userInfo.candidate_question) {
      setIsInitialLoad(false);
      setIsLoading(true);
      setStartTime(new Date());
      handleAnalysis();
    }
  }, [isInitialLoad, userInfo.candidate_question]);

  const handleAnalysis = async () => {
    try {
      const result = await runWorkflow(userInfo);
      setResponse(result.final_answer);
      toast.success('분석이 완료되었습니다!');
    } catch (error) {
      console.error('Failed to get response:', error);
      toast.error('분석 중 오류가 발생했습니다.');
      setResponse('죄송합니다. 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
      setStartTime(null);
      setElapsedTime(0);
    }
  };

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <motion.section
      className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      {/* 헤더 */}
      <div className="text-center mb-12">
        <motion.h2
          className="text-3xl font-bold text-secondary-800 mb-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          AI 커리어 분석 결과
        </motion.h2>
        <motion.p
          className="text-lg text-secondary-600"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          입력해주신 정보를 바탕으로 맞춤형 분석을 제공해드립니다
        </motion.p>
      </div>

      {/* 질문 카드 */}
      <motion.div
        className="bg-white rounded-xl shadow-lg border border-secondary-200 p-6 mb-8"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="w-12 h-12 bg-gradient-to-r from-primary-600 to-primary-700 rounded-full flex items-center justify-center">
              <MessageCircle className="w-6 h-6 text-white" />
            </div>
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-secondary-800 mb-2">
              귀하의 질문
            </h3>
            <p className="text-secondary-600 leading-relaxed">
              {userInfo.candidate_question}
            </p>
          </div>
        </div>
      </motion.div>

      {/* 응답 영역 */}
      <AnimatePresence mode="wait">
        {isLoading ? (
          <motion.div
            key="loading"
            className="bg-white rounded-xl shadow-lg border border-secondary-200 p-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.5 }}
          >
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-primary-600 to-primary-700 rounded-full mb-6">
                <Loader2 className="w-8 h-8 text-white animate-spin" />
              </div>
              
              <h3 className="text-xl font-semibold text-secondary-800 mb-4">
                AI가 분석하고 있습니다...
              </h3>
              
              <div className="space-y-3 mb-6">
                <div className="flex items-center justify-center space-x-2 text-secondary-600">
                  <Clock className="w-4 h-4" />
                  <span>경과 시간: {formatTime(elapsedTime)}</span>
                </div>
                <p className="text-secondary-500">
                  최고의 답변을 위해 심층 분석 중입니다. 잠시만 기다려주세요.
                </p>
              </div>

              {/* 진행 단계 표시 */}
              <div className="space-y-3">
                <div className="flex items-center justify-center space-x-2 text-sm">
                  <div className="w-2 h-2 bg-primary-600 rounded-full animate-pulse" />
                  <span className="text-secondary-600">관련 정보 수집 중...</span>
                </div>
                <div className="flex items-center justify-center space-x-2 text-sm">
                  <div className="w-2 h-2 bg-primary-400 rounded-full animate-pulse delay-200" />
                  <span className="text-secondary-600">데이터 분석 중...</span>
                </div>
                <div className="flex items-center justify-center space-x-2 text-sm">
                  <div className="w-2 h-2 bg-primary-300 rounded-full animate-pulse delay-500" />
                  <span className="text-secondary-600">맞춤형 답변 생성 중...</span>
                </div>
              </div>
            </div>
          </motion.div>
        ) : response ? (
          <motion.div
            key="response"
            className="bg-white rounded-xl shadow-lg border border-secondary-200 overflow-hidden"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            {/* 응답 헤더 */}
            <div className="bg-gradient-to-r from-emerald-600 to-teal-600 px-6 py-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="text-white font-semibold">분석 완료</h3>
                  <p className="text-emerald-100 text-sm">맞춤형 커리어 조언</p>
                </div>
              </div>
            </div>

            {/* 응답 내용 */}
            <div className="p-6">
              <div className="prose prose-lg max-w-none">
                <div className="text-secondary-800 leading-relaxed whitespace-pre-wrap">
                  {response}
                </div>
              </div>
            </div>

            {/* 추가 액션 */}
            <div className="bg-secondary-50 px-6 py-4 border-t border-secondary-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-sm text-secondary-600">
                  <Sparkles className="w-4 h-4" />
                  <span>AI 기반 맞춤형 분석 완료</span>
                </div>
                <button
                  onClick={() => window.location.reload()}
                  className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                >
                  새로운 질문하기
                </button>
              </div>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>

      {/* 도움말 */}
      {!isLoading && response && (
        <motion.div
          className="mt-8 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
        >
          <p className="text-sm text-secondary-500">
            💡 더 궁금한 점이 있으시면 새로운 질문으로 다시 문의해주세요.
          </p>
        </motion.div>
      )}
    </motion.section>
  );
};

export default ResponseSection; 