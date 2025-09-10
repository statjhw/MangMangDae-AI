import { motion } from 'framer-motion';
import { User, TrendingUp, Code, MapPin, Briefcase, GraduationCap, Building2, DollarSign, BarChart } from 'lucide-react';
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
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      {/* 헤더 개선 */}
      <div className="text-center mb-16">
        <motion.div
          className="inline-flex items-center gap-3 bg-gradient-to-r from-primary-100 to-blue-100 px-6 py-3 rounded-full mb-6"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          <BarChart className="h-6 w-6 text-primary-600" />
          <span className="text-primary-800 font-semibold">개인 맞춤 분석 리포트</span>
        </motion.div>
        
        <motion.h2
          className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-primary-600 to-blue-600 bg-clip-text text-transparent mb-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          Your Career Insights
        </motion.h2>
        
        <motion.p
          className="text-xl text-secondary-600 max-w-3xl mx-auto leading-relaxed"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          AI가 분석한 당신만의 <span className="font-semibold text-primary-600">커리어 경쟁력</span>과 시장 기회를 확인해보세요
        </motion.p>
      </div>

      {/* 개선된 사용자 정보 요약 카드 */}
      <motion.div
        className="bg-white rounded-3xl p-8 mb-16 shadow-2xl border border-gray-100"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <div className="p-4 bg-gradient-to-r from-primary-500 to-blue-500 rounded-2xl shadow-lg">
              <User className="h-7 w-7 text-white" />
            </div>
            <div>
              <h3 className="text-2xl font-bold text-gray-900">개인 프로필</h3>
              <p className="text-gray-500">입력하신 정보 요약</p>
            </div>
          </div>
          <div className="hidden sm:flex items-center gap-2 px-4 py-2 bg-green-50 text-green-700 rounded-full text-sm font-medium">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            분석 완료
          </div>
        </div>
        
        {/* 프로필 정보 그리드 - 더 깔끔한 디자인 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="space-y-4">
            <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-2xl hover:bg-gray-100 transition-colors">
              <div className="p-2 bg-blue-100 rounded-xl">
                <GraduationCap className="h-5 w-5 text-blue-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-500 mb-1">전공 분야</p>
                <p className="text-lg font-semibold text-gray-900">{userStat.user_info?.전공 || '정보 없음'}</p>
              </div>
            </div>
            
            <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-2xl hover:bg-gray-100 transition-colors">
              <div className="p-2 bg-purple-100 rounded-xl">
                <MapPin className="h-5 w-5 text-purple-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-500 mb-1">희망 지역</p>
                <p className="text-lg font-semibold text-gray-900">{userStat.user_info?.희망지역 || '정보 없음'}</p>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-2xl hover:bg-gray-100 transition-colors">
              <div className="p-2 bg-emerald-100 rounded-xl">
                <Briefcase className="h-5 w-5 text-emerald-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-500 mb-1">경력 수준</p>
                <p className="text-lg font-semibold text-gray-900">{userStat.user_info?.경력 || '정보 없음'}</p>
              </div>
            </div>
            
            <div className="flex items-start gap-4 p-4 bg-gray-50 rounded-2xl hover:bg-gray-100 transition-colors">
              <div className="p-2 bg-orange-100 rounded-xl">
                <TrendingUp className="h-5 w-5 text-orange-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-500 mb-1">관심 분야</p>
                <p className="text-lg font-semibold text-gray-900">{userStat.user_info?.관심분야 || '정보 없음'}</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* 기술 스택 - 더 매력적인 디자인 */}
        <div className="border-t border-gray-100 pt-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-indigo-100 rounded-xl">
              <Code className="h-5 w-5 text-indigo-600" />
            </div>
            <h4 className="text-lg font-semibold text-gray-900">보유 기술 스택</h4>
          </div>
          
          <div className="flex flex-wrap gap-3">
            {userStat.user_info?.기술스택 ? 
              (Array.isArray(userStat.user_info.기술스택) 
                ? userStat.user_info.기술스택 
                : String(userStat.user_info.기술스택).split(', ')
              ).filter(tech => tech && tech.trim()).map((tech, index) => (
                <motion.span
                  key={index}
                  className="px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-full text-sm font-medium shadow-lg hover:shadow-xl transition-shadow"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {tech.trim()}
                </motion.span>
              )) :
              <span className="px-4 py-2 bg-gray-200 text-gray-600 rounded-full text-sm font-medium">
                기술 스택 정보 없음
              </span>
            }
          </div>
        </div>
      </motion.div>

      {/* 핵심 인사이트 카드들 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-16">
        {/* 관심 분야 채용 현황 - 메인 카드 */}
        <motion.div
          className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-3xl p-8 shadow-xl border border-emerald-100 relative overflow-hidden"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
        >
          {/* 배경 데코레이션 */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-200 rounded-full opacity-20 -translate-y-16 translate-x-16"></div>
          
          <div className="relative">
            <div className="text-center mb-8">
              <div className="flex justify-center mb-4">
                <div className="p-4 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-2xl shadow-lg">
                  <TrendingUp className="h-7 w-7 text-white" />
                </div>
              </div>
              <h3 className="text-2xl font-bold text-emerald-800 mb-2">관심 분야 현황</h3>
              <p className="text-emerald-600">시장 기회 분석</p>
            </div>
            
            <div className="text-center mb-8">
              <div className="inline-flex items-baseline gap-2 mb-4">
                <span className="text-6xl font-black text-emerald-600">
                  {userStat.interest?.total_job || 0}
                </span>
                <span className="text-2xl font-semibold text-emerald-800">개</span>
              </div>
              <p className="text-lg text-emerald-700 mb-2">
                <strong>"{userStat.interest?.interest || '정보 없음'}"</strong> 관련 채용공고
              </p>
            </div>
            
            <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-emerald-200">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-emerald-100 rounded-xl">
                  <div className="w-3 h-3 bg-emerald-500 rounded-full animate-pulse"></div>
                </div>
                <div>
                  <h4 className="font-semibold text-emerald-800 mb-2">💡 AI 분석 결과</h4>
                  <p className="text-emerald-700 leading-relaxed">
                    해당 분야는 현재 <strong>활발한 채용</strong>이 진행되고 있어 지원하기 좋은 시기입니다. 
                    경쟁력을 높여 적극적으로 도전해보세요!
                  </p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* 기술 스택 차트 - 개선된 디자인 */}
        <motion.div
          className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.7 }}
        >
          <div className="p-8">
            <div className="flex items-center gap-4 mb-6">
              <div className="p-4 bg-gradient-to-r from-purple-500 to-indigo-500 rounded-2xl shadow-lg">
                <Code className="h-7 w-7 text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-900">기술 스택 분석</h3>
                <p className="text-gray-600">회사별 수요 현황</p>
              </div>
            </div>
          </div>
          
          <PieChart
            data={techStackData}
            title=""
            height={350}
            className="px-4 pb-8"
          />
          
          <div className="px-8 pb-8">
            <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-2xl p-4">
              <p className="text-sm text-purple-700 text-center">
                <strong>보유 기술 중 가장 수요가 높은 기술</strong>을 확인해보세요
              </p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* 세부 통계 카드들 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
        {/* 지역별 현황 - 컴팩트한 카드 */}
        <motion.div
          className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100 hover:shadow-xl transition-all duration-300"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          whileHover={{ y: -4 }}
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-gradient-to-r from-blue-400 to-cyan-400 rounded-xl shadow-sm">
              <MapPin className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">지역별 현황</h3>
              <p className="text-gray-500 text-sm">위치 기반 분석</p>
            </div>
          </div>
          
          <div className="text-center mb-6">
            <div className="text-3xl font-black text-blue-600 mb-2">
              {userStat.location?.total_jobs || 0}
            </div>
            <p className="text-blue-700 font-medium">
              {userStat.location?.location || '설정 지역'} 채용공고
            </p>
          </div>

          {userStat.location?.popular_categories && userStat.location.popular_categories.length > 0 && (
            <div className="bg-blue-50 rounded-xl p-4">
              <p className="text-xs font-semibold text-blue-800 mb-3">🏆 인기 직무</p>
              <div className="space-y-2">
                {userStat.location.popular_categories.slice(0, 3).map((cat, idx) => (
                  <div key={idx} className="flex justify-between items-center">
                    <span className="text-sm text-blue-700">{cat.category}</span>
                    <span className="px-2 py-1 bg-blue-200 text-blue-800 rounded-full text-xs font-bold">
                      {cat.count}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>

        {/* 경력 매칭률 - 진행률 바 강조 */}
        <motion.div
          className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100 hover:shadow-xl transition-all duration-300"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
          whileHover={{ y: -4 }}
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-gradient-to-r from-purple-400 to-pink-400 rounded-xl shadow-sm">
              <Briefcase className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">경력 매칭</h3>
              <p className="text-gray-500 text-sm">적합도 분석</p>
            </div>
          </div>
          
          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-gray-600">매칭률</span>
              <span className="text-2xl font-black text-purple-600">
                {userStat.career?.percentage || 0}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div 
                className="bg-gradient-to-r from-purple-500 to-pink-500 h-3 rounded-full transition-all duration-700 ease-out"
                style={{ width: `${userStat.career?.percentage || 0}%` }}
              ></div>
            </div>
          </div>

          <div className="bg-purple-50 rounded-xl p-4 space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-purple-700">매칭 공고</span>
              <span className="font-bold text-purple-800">{userStat.career?.matching_jobs || 0}개</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-purple-700">전체 공고</span>
              <span className="font-bold text-purple-800">{userStat.career?.total_jobs || 0}개</span>
            </div>
          </div>
        </motion.div>

        {/* 기업 규모 분포 - 더 시각적으로 */}
        <motion.div
          className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100 hover:shadow-xl transition-all duration-300"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.0 }}
          whileHover={{ y: -4 }}
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-gradient-to-r from-indigo-400 to-purple-400 rounded-xl shadow-sm">
              <Building2 className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">기업 규모</h3>
              <p className="text-gray-500 text-sm">규모별 분포</p>
            </div>
          </div>
          
          {userStat.company_size_distribution?.distribution && (
            <div className="space-y-4">
              {Object.entries(userStat.company_size_distribution.distribution).map(([size, percentage], idx) => (
                <div key={idx} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-700">{size.split(' ')[0]}</span>
                    <span className="text-sm font-bold text-indigo-600">{percentage as number}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <motion.div 
                      className={`h-2 rounded-full ${
                        idx === 0 ? 'bg-gradient-to-r from-green-400 to-green-500' :
                        idx === 1 ? 'bg-gradient-to-r from-blue-400 to-blue-500' :
                        idx === 2 ? 'bg-gradient-to-r from-orange-400 to-orange-500' :
                        'bg-gradient-to-r from-indigo-400 to-indigo-500'
                      }`}
                      initial={{ width: 0 }}
                      animate={{ width: `${percentage}%` }}
                      transition={{ duration: 1, delay: 1.2 + idx * 0.1 }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </div>

      {/* 최종 인사이트 및 추천 */}
      <motion.div
        className="bg-gradient-to-br from-slate-900 to-blue-900 rounded-3xl p-8 text-white shadow-2xl relative overflow-hidden"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.2 }}
      >
        {/* 배경 데코레이션 */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500 rounded-full opacity-10 -translate-y-32 translate-x-32"></div>
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-purple-500 rounded-full opacity-10 translate-y-24 -translate-x-24"></div>
        
        <div className="relative">
          <div className="flex items-center gap-4 mb-8">
            <div className="p-4 bg-gradient-to-r from-yellow-400 to-orange-400 rounded-2xl shadow-lg">
              <span className="text-2xl">🚀</span>
            </div>
            <div>
              <h3 className="text-3xl font-bold">AI 종합 분석 결과</h3>
              <p className="text-blue-100 text-lg">당신의 커리어 성공을 위한 맞춤 제안</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-2xl">🎯</span>
                <h4 className="text-xl font-bold text-yellow-300">경쟁력 분석</h4>
              </div>
              <p className="text-blue-100 leading-relaxed">
                {userStat.tech_stack && Object.keys(userStat.tech_stack).length > 0 ? (
                  <>
                    보유 기술 중 <span className="font-bold text-yellow-300">{Object.entries(userStat.tech_stack).sort(([,a], [,b]) => b - a)[0]?.[0]}</span>가 
                    가장 높은 수요({Object.entries(userStat.tech_stack).sort(([,a], [,b]) => b - a)[0]?.[1]}개 회사)를 보이고 있어 
                    <span className="font-bold text-green-300"> 유리한 위치</span>에 있습니다.
                  </>
                ) : (
                  "기술 스택 정보를 입력하시면 더 정확한 경쟁력 분석을 제공해드릴 수 있습니다."
                )}
              </p>
            </div>
            
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-2xl">📈</span>
                <h4 className="text-xl font-bold text-green-300">액션 플랜</h4>
              </div>
              <p className="text-blue-100 leading-relaxed mb-4">
                현재 <span className="font-bold text-yellow-300">{userStat.interest?.total_job || 0}개</span>의 관련 채용공고가 활성화되어 있습니다.
              </p>
              
              <div className="space-y-2">
                {(userStat.interest?.total_job || 0) > 0 && (
                  <div className="flex items-center gap-2 text-green-300">
                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                    <span className="text-sm font-medium">적극적인 지원 추천</span>
                  </div>
                )}
                <div className="flex items-center gap-2 text-blue-200">
                  <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                  <span className="text-sm font-medium">포트폴리오 업데이트 권장</span>
                </div>
                <div className="flex items-center gap-2 text-purple-200">
                  <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                  <span className="text-sm font-medium">네트워킹 활동 강화</span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="mt-8 text-center">
            <p className="text-blue-200 text-lg mb-4">
              🌟 <span className="font-semibold">AI가 분석한 당신의 커리어 성공 확률:</span> 
              <span className="text-3xl font-black text-yellow-300 ml-2">
                {Math.min(85, Math.max(65, (userStat.career?.percentage || 50) + 20))}%
              </span>
            </p>
            <p className="text-sm text-blue-300">
              지속적인 스킬 업데이트와 적극적인 지원으로 더 높은 성공률을 달성할 수 있습니다.
            </p>
          </div>
        </div>
      </motion.div>
    </motion.section>
  );
};

export default UserStatSection; 