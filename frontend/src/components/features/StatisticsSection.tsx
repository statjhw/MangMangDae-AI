import { motion } from 'framer-motion';
import { TrendingUp, Users, MapPin, DollarSign } from 'lucide-react';
import BarChart from '../charts/BarChart';
import PieChart from '../charts/PieChart';
import { Statistics } from '../../types';

interface StatisticsSectionProps {
  statistics: Statistics;
  loading?: boolean;
}

const StatisticsSection = ({ statistics, loading = false }: StatisticsSectionProps) => {
  if (loading) {
    return (
      <motion.div
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-secondary-600">통계 데이터를 분석하고 있습니다...</p>
        </div>
      </motion.div>
    );
  }

  // 차트 데이터 변환
  const jobPreferencesData = statistics.jobPreferences.map(item => ({
    name: item.job,
    value: item.percentage,
  }));

  const salaryDistributionData = statistics.salaryDistribution.map(item => ({
    name: item.range,
    value: item.count,
  }));

  const locationRatioData = statistics.locationRatio.map(item => ({
    name: item.location,
    value: item.ratio,
  }));

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
          맞춤형 통계 분석
        </motion.h2>
        <motion.p
          className="text-lg text-secondary-600 max-w-2xl mx-auto"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          입력하신 정보를 바탕으로 시장 동향과 경쟁력을 분석해드립니다
        </motion.p>
      </div>

      {/* 주요 지표 카드 */}
      <motion.div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <motion.div
          className="bg-white rounded-xl p-6 shadow-lg border border-secondary-100"
          whileHover={{ y: -5, boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)' }}
          transition={{ duration: 0.3 }}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-secondary-600">평균 연봉</p>
              <p className="text-2xl font-bold text-secondary-800">
                {statistics.averageSalary.toLocaleString()}만원
              </p>
            </div>
            <div className="p-3 bg-primary-100 rounded-lg">
              <DollarSign className="h-6 w-6 text-primary-600" />
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-white rounded-xl p-6 shadow-lg border border-secondary-100"
          whileHover={{ y: -5, boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)' }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-secondary-600">인기 직무</p>
              <p className="text-2xl font-bold text-secondary-800">
                {statistics.jobPreferences[0]?.job || 'N/A'}
              </p>
            </div>
            <div className="p-3 bg-emerald-100 rounded-lg">
              <TrendingUp className="h-6 w-6 text-emerald-600" />
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-white rounded-xl p-6 shadow-lg border border-secondary-100"
          whileHover={{ y: -5, boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)' }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-secondary-600">선호 지역</p>
              <p className="text-2xl font-bold text-secondary-800">
                {statistics.locationRatio[0]?.location || 'N/A'}
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <MapPin className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </motion.div>

        <motion.div
          className="bg-white rounded-xl p-6 shadow-lg border border-secondary-100"
          whileHover={{ y: -5, boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)' }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-secondary-600">시장 점유율</p>
              <p className="text-2xl font-bold text-secondary-800">
                {statistics.jobPreferences[0]?.percentage || 0}%
              </p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <Users className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* 차트 섹션 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
        >
          <BarChart
            data={jobPreferencesData}
            title="인기 직무 분포"
            xAxisLabel="직무"
            yAxisLabel="선호도 (%)"
            height={300}
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
        >
          <PieChart
            data={salaryDistributionData}
            title="연봉 분포"
            height={300}
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.7 }}
        >
          <BarChart
            data={locationRatioData}
            title="지역별 채용 비율"
            xAxisLabel="지역"
            yAxisLabel="비율 (%)"
            height={300}
          />
        </motion.div>

        <motion.div
          className="bg-white rounded-xl p-6 shadow-lg"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.8 }}
        >
          <h3 className="text-lg font-semibold text-secondary-800 mb-4">시장 인사이트</h3>
          <div className="space-y-4">
            <div className="p-4 bg-primary-50 rounded-lg">
              <h4 className="font-medium text-primary-800 mb-2">💡 주요 트렌드</h4>
              <p className="text-sm text-primary-700">
                {statistics.jobPreferences[0]?.job} 직무가 현재 가장 높은 수요를 보이고 있으며, 
                평균 연봉은 {statistics.averageSalary.toLocaleString()}만원 수준입니다.
              </p>
            </div>
            
            <div className="p-4 bg-emerald-50 rounded-lg">
              <h4 className="font-medium text-emerald-800 mb-2">🎯 경쟁력 분석</h4>
              <p className="text-sm text-emerald-700">
                {statistics.locationRatio[0]?.location} 지역에서 가장 많은 채용이 이루어지고 있으며, 
                해당 지역의 시장 점유율은 {statistics.locationRatio[0]?.ratio}%입니다.
              </p>
            </div>
            
            <div className="p-4 bg-amber-50 rounded-lg">
              <h4 className="font-medium text-amber-800 mb-2">📈 성장 전망</h4>
              <p className="text-sm text-amber-700">
                최근 3년간 해당 직무의 성장률은 연평균 15%를 기록하고 있으며, 
                향후 5년간 지속적인 성장이 예상됩니다.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </motion.section>
  );
};

export default StatisticsSection; 