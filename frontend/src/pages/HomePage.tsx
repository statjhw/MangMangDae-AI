import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, TrendingUp, Users, Zap, ArrowRight, Star } from 'lucide-react';
import UserInfoForm from '../components/features/UserInfoForm';
import ResponseSection from '../components/features/ChatSection';
import Button from '../components/common/Button';
import { UserInfo } from '../types';
import toast from 'react-hot-toast';

const HomePage = () => {
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [currentSection, setCurrentSection] = useState<'form' | 'response'>('form');
  const [isAnalysisStarted, setIsAnalysisStarted] = useState(false);
  const [showResponseSection, setShowResponseSection] = useState(false);



  const handleAnalysisStart = async (data: UserInfo) => {
    setUserInfo(data);
    setIsAnalysisStarted(true);
    setShowResponseSection(true);
    toast.success('AI 분석을 시작합니다!');
    
    // 바로 응답 섹션으로 이동
    setTimeout(() => {
      scrollToSection('response');
    }, 100);
  };

  const scrollToSection = (section: 'form' | 'response') => {
    setCurrentSection(section);
    if (section === 'response') {
      setShowResponseSection(true);
    }
    const element = document.getElementById(section);
    if (element) {
      if (section === 'response') {
        // 응답 섹션으로는 즉시 이동
        const elementTop = element.offsetTop;
        window.scrollTo({
          top: elementTop,
          behavior: 'auto'
        });
      } else {
        // 다른 섹션으로는 부드럽게 이동
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  return (
    <div className="min-h-screen">
      {/* 히어로 섹션 */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-600 via-primary-700 to-primary-800 text-white py-20">
        {/* 배경 애니메이션 요소 */}
        <div className="absolute inset-0 overflow-hidden">
          <motion.div
            className="absolute top-20 left-20 w-32 h-32 bg-white/10 rounded-full"
            animate={{ y: [0, -20, 0] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            className="absolute top-40 right-32 w-24 h-24 bg-white/5 rounded-full"
            animate={{ y: [0, 20, 0] }}
            transition={{ duration: 8, repeat: Infinity, ease: "easeInOut", delay: 2 }}
          />
          <motion.div
            className="absolute bottom-20 left-1/3 w-16 h-16 bg-white/15 rounded-full"
            animate={{ y: [0, -15, 0] }}
            transition={{ duration: 7, repeat: Infinity, ease: "easeInOut", delay: 1 }}
          />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="inline-flex items-center space-x-2 bg-white/20 backdrop-blur-sm rounded-full px-6 py-2 mb-8">
              <Brain className="h-5 w-5" />
              <span className="text-sm font-medium">AI 기반 커리어 분석</span>
            </div>
            
            <h1 className="text-5xl md:text-6xl font-bold mb-6">
              MMD
              <span className="block text-3xl md:text-4xl font-normal mt-2 text-primary-100">
                망망대 AI
              </span>
            </h1>
            
            <p className="text-xl md:text-2xl text-primary-100 mb-8 max-w-3xl mx-auto">
              당신의 정보를 바탕으로 맞춤형 통계와 AI 상담을 제공하는 
              <span className="font-semibold"> 스마트 커리어 플랫폼</span>
            </p>
            
            <motion.button
              className="bg-white text-primary-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-primary-50 transition-colors duration-200 inline-flex items-center space-x-2"
              onClick={() => scrollToSection('form')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <span>시작하기</span>
              <ArrowRight className="h-5 w-5" />
            </motion.button>
          </motion.div>
        </div>
      </section>

      {/* 기능 소개 섹션 */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-secondary-800 mb-4">
              왜 MMD인가요?
            </h2>
            <p className="text-lg text-secondary-600 max-w-2xl mx-auto">
              최신 AI 기술과 빅데이터를 활용하여 개인 맞춤형 커리어 분석을 제공합니다
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                icon: TrendingUp,
                title: '실시간 통계 분석',
                description: '입력하신 정보를 바탕으로 시장 동향과 경쟁력을 실시간으로 분석합니다.',
                color: 'text-blue-600',
                bgColor: 'bg-blue-100',
              },
              {
                icon: Brain,
                title: 'AI 기반 상담',
                description: 'RAG 기술을 활용한 지능형 AI가 커리어 관련 질문에 답변해드립니다.',
                color: 'text-purple-600',
                bgColor: 'bg-purple-100',
              },
              {
                icon: Users,
                title: '개인 맞춤 추천',
                description: '학력, 경력, 선호도를 고려한 개인화된 직무 추천을 제공합니다.',
                color: 'text-green-600',
                bgColor: 'bg-green-100',
              },
            ].map((feature, index) => (
              <motion.div
                key={index}
                className="text-center p-8 rounded-xl bg-secondary-50 hover:bg-white hover:shadow-lg transition-all duration-300"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                viewport={{ once: true }}
                whileHover={{ y: -5 }}
              >
                <div className={`inline-flex p-4 rounded-full ${feature.bgColor} mb-6`}>
                  <feature.icon className={`h-8 w-8 ${feature.color}`} />
                </div>
                <h3 className="text-xl font-semibold text-secondary-800 mb-4">
                  {feature.title}
                </h3>
                <p className="text-secondary-600">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* 사용자 정보 입력 폼 */}
      <section id="form" className="py-20 bg-gradient-to-br from-secondary-50 to-primary-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center mb-12"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-secondary-800 mb-4">
              정보를 입력해주세요
            </h2>
            <p className="text-lg text-secondary-600">
              더 정확한 분석을 위해 몇 가지 정보가 필요합니다
            </p>
          </motion.div>

          <UserInfoForm onSubmit={handleAnalysisStart} />
        </div>
      </section>



      {/* 응답 섹션 */}
      <AnimatePresence>
        {userInfo && isAnalysisStarted && showResponseSection && (
          <section id="response" className="py-20 bg-gradient-to-br from-primary-50 to-secondary-50">
            <ResponseSection userInfo={userInfo} />
          </section>
        )}
      </AnimatePresence>

      {/* 푸터 */}
      <footer className="bg-secondary-800 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <Brain className="h-6 w-6 text-primary-400" />
              <span className="text-xl font-bold">MMD</span>
            </div>
            <p className="text-secondary-300 mb-4">
              망망대 AI - 스마트한 커리어 분석 플랫폼
            </p>
            <div className="flex items-center justify-center space-x-1 text-yellow-400">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="h-4 w-4 fill-current" />
              ))}
              <span className="ml-2 text-secondary-300">4.9/5.0</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage; 