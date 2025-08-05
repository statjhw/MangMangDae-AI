import { motion } from 'framer-motion';
import { Brain, Sparkles } from 'lucide-react';

const Header = () => {
  return (
    <motion.header 
      className="sticky top-0 z-50 glass-effect border-b border-white/20"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* 로고 */}
          <motion.div 
            className="flex items-center space-x-2"
            whileHover={{ scale: 1.05 }}
            transition={{ duration: 0.2 }}
          >
            <div className="relative">
              <Brain className="h-8 w-8 text-primary-600" />
              <Sparkles className="h-4 w-4 text-primary-400 absolute -top-1 -right-1" />
            </div>
            <div className="flex flex-col">
              <h1 className="text-xl font-bold gradient-text">MMD</h1>
              <p className="text-xs text-secondary-500 -mt-1">망망대 AI</p>
            </div>
          </motion.div>

          {/* 네비게이션 */}
          <nav className="hidden md:flex items-center space-x-8">
            <motion.a 
              href="#home" 
              className="text-secondary-700 hover:text-primary-600 transition-colors duration-200"
              whileHover={{ y: -2 }}
            >
              홈
            </motion.a>
            <motion.a 
              href="#features" 
              className="text-secondary-700 hover:text-primary-600 transition-colors duration-200"
              whileHover={{ y: -2 }}
            >
              기능
            </motion.a>
            <motion.a 
              href="#about" 
              className="text-secondary-700 hover:text-primary-600 transition-colors duration-200"
              whileHover={{ y: -2 }}
            >
              소개
            </motion.a>
          </nav>

          {/* CTA 버튼 */}
          <motion.button
            className="btn-primary hidden sm:block"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            시작하기
          </motion.button>
        </div>
      </div>
    </motion.header>
  );
};

export default Header; 