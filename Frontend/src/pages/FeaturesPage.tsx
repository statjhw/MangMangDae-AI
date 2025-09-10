import { motion } from 'framer-motion';
import { 
  Brain, 
  Search, 
  BarChart3, 
  Users, 
  MapPin, 
  Building2,
  Sparkles,
  MessageCircle
} from 'lucide-react';

const FeaturesPage = () => {
  const features = [
    {
      icon: Brain,
      title: "AI 기반 맞춤 추천",
      description: "사용자의 전공, 경력, 관심사, 위치, 기술 스택을 분석하여 최적의 채용공고를 추천합니다.",
      highlights: ["개인화된 분석", "LangGraph 워크플로우", "실시간 매칭"]
    },
    {
      icon: MessageCircle,
      title: "대화형 채용 상담",
      description: "궁금한 점을 자연어로 질문하면 AI가 상세하고 도움이 되는 답변을 제공합니다.",
      highlights: ["자연어 처리", "즉시 응답", "연속 대화"]
    },
    {
      icon: Search,
      title: "스마트 채용공고 검색",
      description: "OpenSearch를 활용한 벡터 검색으로 의미적으로 관련된 채용공고를 찾아줍니다.",
      highlights: ["벡터 검색", "의미 기반 매칭", "고도화된 필터링"]
    },
    {
      icon: BarChart3,
      title: "실시간 통계 분석",
      description: "현재 채용 시장의 트렌드와 나의 프로필 경쟁력을 한눈에 파악할 수 있습니다.",
      highlights: ["시장 트렌드", "개인 통계", "경쟁력 분석"]
    },
    {
      icon: MapPin,
      title: "지역별 채용 정보",
      description: "원하는 지역의 채용 동향과 기회를 지역별로 상세하게 분석해드립니다.",
      highlights: ["지역별 분석", "위치 기반 추천", "교통편 고려"]
    },
    {
      icon: Building2,
      title: "기업 정보 제공",
      description: "관심 있는 기업의 상세 정보, 채용 패턴, 복리후생 등을 종합적으로 제공합니다.",
      highlights: ["기업 분석", "채용 패턴", "복리후생 정보"]
    }
  ];


  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 pt-16">
      {/* Hero Section */}
      <section className="pt-20 pb-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div 
            className="text-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="flex justify-center mb-6">
              <Sparkles className="h-16 w-16 text-primary-600" />
            </div>
            <h1 className="text-4xl md:text-6xl font-bold gradient-text mb-6">
              AI가 제공하는<br />스마트 채용 솔루션
            </h1>
            <p className="text-xl text-secondary-600 max-w-3xl mx-auto mb-8">
              망망대 AI는 최신 인공지능 기술을 활용하여 
              당신의 꿈의 직장을 찾아드립니다
            </p>
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div 
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-secondary-800 mb-4">
              주요 기능
            </h2>
            <p className="text-secondary-600 max-w-2xl mx-auto">
              망망대 AI가 제공하는 혁신적인 채용 서비스 기능들을 확인해보세요
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                className="glass-card p-8 rounded-2xl border border-white/20 hover:border-primary-200 transition-all duration-300"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                whileHover={{ y: -4, scale: 1.02 }}
              >
                <div className="flex items-center mb-6">
                  <div className="p-3 bg-primary-100 rounded-xl mr-4">
                    <feature.icon className="h-6 w-6 text-primary-600" />
                  </div>
                  <h3 className="text-xl font-bold text-secondary-800">
                    {feature.title}
                  </h3>
                </div>
                
                <p className="text-secondary-600 mb-6 leading-relaxed">
                  {feature.description}
                </p>
                
                <ul className="space-y-2">
                  {feature.highlights.map((highlight, idx) => (
                    <li key={idx} className="flex items-center text-sm text-secondary-700">
                      <div className="w-1.5 h-1.5 bg-primary-500 rounded-full mr-3"></div>
                      {highlight}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Technology Section */}
      <section className="py-20 bg-gradient-to-r from-primary-50 to-blue-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div 
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-secondary-800 mb-4">
              사용 기술
            </h2>
            <p className="text-secondary-600 max-w-2xl mx-auto">
              최신 AI 기술과 검증된 플랫폼을 기반으로 구축된 서비스입니다
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { name: "LangGraph", desc: "AI 워크플로우" },
              { name: "OpenSearch", desc: "벡터 검색" },
              { name: "Claude AI", desc: "자연어 처리" },
              { name: "React", desc: "사용자 인터페이스" }
            ].map((tech, index) => (
              <motion.div
                key={tech.name}
                className="text-center p-6 bg-white/80 rounded-xl backdrop-blur-sm"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                whileHover={{ scale: 1.05 }}
              >
                <div className="text-lg font-bold text-secondary-800 mb-2">
                  {tech.name}
                </div>
                <div className="text-secondary-600 text-sm">
                  {tech.desc}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-secondary-800 mb-6">
              지금 바로 시작하세요
            </h2>
            <p className="text-secondary-600 mb-8 text-lg">
              망망대 AI와 함께 당신의 커리어 여정을 시작해보세요
            </p>
            <motion.button
              className="btn-primary btn-lg"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => {
                window.scrollTo({ top: 0, behavior: 'smooth' });
                // 홈페이지로 이동하는 로직 추가 가능
              }}
            >
              무료로 시작하기
            </motion.button>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default FeaturesPage;