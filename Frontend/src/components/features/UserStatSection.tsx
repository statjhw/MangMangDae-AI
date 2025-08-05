import { motion } from 'framer-motion';
import { User, TrendingUp, Code, MapPin, Briefcase, GraduationCap } from 'lucide-react';
import PieChart from '../charts/PieChart';
import { UserStatResponse } from '../../types';

interface UserStatSectionProps {
  userStat: UserStatResponse | null;
  loading?: boolean;
}

const UserStatSection = ({ userStat, loading = false }: UserStatSectionProps) => {
  if (loading) {
    return (
      <motion.div
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-secondary-600">맞춤형 통계를 생성하고 있습니다...</p>
        </div>
      </motion.div>
    );
  }

  if (!userStat) {
    return (
      <motion.div
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <p className="text-secondary-600">통계 데이터를 불러오지 못했습니다.</p>
      </motion.div>
    );
  }

  // 기술 스택 차트 데이터 변환
  const techStackData = userStat.tech_stack ? Object.entries(userStat.tech_stack).map(([tech, count], index) => ({
    name: tech,
    value: count,
    color: [
      '#3776ab', '#61dafb', '#ed8b00', '#e34c26', '#f7df1e', 
      '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57'
    ][index % 10]
  })) : [];

  return (
    <motion.section
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="text-center mb-12">
        <motion.h2
          className="text-3xl font-bold text-secondary-800 mb-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          📊 당신의 맞춤형 통계
        </motion.h2>
        <motion.p
          className="text-lg text-secondary-600 max-w-2xl mx-auto"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          입력하신 정보를 바탕으로 분석한 맞춤형 시장 데이터입니다
        </motion.p>
      </div>

      {/* 사용자 정보 요약 카드 */}
      <motion.div
        className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-2xl p-8 mb-12 border border-primary-100"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="p-3 bg-primary-600 rounded-full">
            <User className="h-6 w-6 text-white" />
          </div>
          <h3 className="text-xl font-semibold text-secondary-800">프로필 요약</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="flex items-center gap-3 bg-white/70 rounded-lg p-4">
            <GraduationCap className="h-5 w-5 text-primary-600" />
            <div>
              <p className="text-sm text-secondary-600">전공</p>
              <p className="font-medium text-secondary-800">{userStat.user_info?.전공 || '정보 없음'}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3 bg-white/70 rounded-lg p-4">
            <Briefcase className="h-5 w-5 text-emerald-600" />
            <div>
              <p className="text-sm text-secondary-600">경력</p>
              <p className="font-medium text-secondary-800">{userStat.user_info?.경력 || '정보 없음'}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3 bg-white/70 rounded-lg p-4">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            <div>
              <p className="text-sm text-secondary-600">관심분야</p>
              <p className="font-medium text-secondary-800">{userStat.user_info?.관심분야 || '정보 없음'}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3 bg-white/70 rounded-lg p-4">
            <MapPin className="h-5 w-5 text-purple-600" />
            <div>
              <p className="text-sm text-secondary-600">희망지역</p>
              <p className="font-medium text-secondary-800">{userStat.user_info?.희망지역 || '정보 없음'}</p>
            </div>
          </div>
        </div>
        
        {/* 기술 스택 태그 */}
        <div className="mt-6">
          <div className="flex items-center gap-2 mb-3">
            <Code className="h-5 w-5 text-indigo-600" />
            <p className="text-sm text-secondary-600 font-medium">보유 기술 스택</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {userStat.user_info?.기술스택 ? 
              (Array.isArray(userStat.user_info.기술스택) 
                ? userStat.user_info.기술스택 
                : String(userStat.user_info.기술스택).split(', ')
              ).filter(tech => tech && tech.trim()).map((tech, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium"
                >
                  {tech.trim()}
                </span>
              )) :
              <span className="px-3 py-1 bg-gray-100 text-gray-500 rounded-full text-sm">
                기술 스택 정보 없음
              </span>
            }
          </div>
        </div>
      </motion.div>

      {/* 통계 데이터 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 관심 분야 채용 정보 */}
        <motion.div
          className="bg-white rounded-xl p-6 shadow-lg border border-secondary-100"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-emerald-100 rounded-lg">
              <TrendingUp className="h-6 w-6 text-emerald-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-secondary-800">관심 분야 채용 현황</h3>
              <p className="text-sm text-secondary-600">현재 시장에서의 채용 정보</p>
            </div>
          </div>
          
                     <div className="text-center py-8">
             <div className="text-4xl font-bold text-emerald-600 mb-2">
               {userStat.interest?.total_job || 0}
             </div>
             <div className="text-lg text-secondary-700 mb-1">개의 채용공고</div>
             <div className="text-sm text-secondary-500">
               "{userStat.interest?.interest || '정보 없음'}" 관련 포지션
             </div>
           </div>
          
          <div className="bg-emerald-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-emerald-700">
              <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
              <span className="text-sm font-medium">시장 전망</span>
            </div>
            <p className="text-sm text-emerald-600 mt-1">
              해당 분야는 현재 활발한 채용이 진행되고 있어 지원하기 좋은 시기입니다.
            </p>
          </div>
        </motion.div>

        {/* 기술 스택별 채용 회사 수 원형 그래프 */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
        >
          <PieChart
            data={techStackData}
            title="🔧 기술 스택별 채용 회사 수"
            height={400}
            className="h-full"
          />
        </motion.div>
      </div>

      {/* 인사이트 카드 */}
      <motion.div
        className="mt-8 bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-6 border border-amber-200"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
      >
        <h3 className="text-lg font-semibold text-amber-800 mb-4 flex items-center gap-2">
          💡 맞춤형 인사이트
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                     <div className="bg-white/70 rounded-lg p-4">
             <h4 className="font-medium text-amber-800 mb-2">🎯 경쟁력 분석</h4>
             <p className="text-sm text-amber-700">
               {userStat.tech_stack && Object.keys(userStat.tech_stack).length > 0 ? (
                 <>
                   보유하신 기술 스택 중 <strong>{Object.entries(userStat.tech_stack).sort(([,a], [,b]) => b - a)[0]?.[0]}</strong>가 
                   가장 많은 회사({Object.entries(userStat.tech_stack).sort(([,a], [,b]) => b - a)[0]?.[1]}개)에서 요구되고 있습니다.
                 </>
               ) : (
                 "기술 스택 정보를 입력하시면 더 정확한 경쟁력 분석을 제공해드릴 수 있습니다."
               )}
             </p>
           </div>
           
           <div className="bg-white/70 rounded-lg p-4">
             <h4 className="font-medium text-amber-800 mb-2">📈 추천 전략</h4>
             <p className="text-sm text-amber-700">
               현재 {userStat.interest?.total_job || 0}개의 관련 채용공고가 있어 
               {(userStat.interest?.total_job || 0) > 0 ? "지원 기회가 풍부합니다. 적극적인 지원을 추천드립니다." : "관련 정보를 확인하고 있습니다."}
             </p>
           </div>
        </div>
      </motion.div>
    </motion.section>
  );
};

export default UserStatSection; 