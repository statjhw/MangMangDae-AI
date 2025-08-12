import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';
import { SessionInfo, SessionStatus } from '../../types';
import { getSessionInfo } from '../../utils/api';

interface SessionStatusIndicatorProps {
  onSessionExpiry?: () => void;
  onSessionRenewal?: () => void;
  className?: string;
}

const SessionStatusIndicator = ({ 
  onSessionExpiry, 
  onSessionRenewal, 
  className = '' 
}: SessionStatusIndicatorProps) => {
  const [, setSessionInfo] = useState<SessionInfo | null>(null);
  const [sessionStatus, setSessionStatus] = useState<SessionStatus>('active');
  const [timeLeft, setTimeLeft] = useState<number>(0);
  const [, setIsVisible] = useState(false);

  // Fetch session info periodically
  useEffect(() => {
    const fetchSessionInfo = async () => {
      try {
        console.log('🔍 SessionStatusIndicator: Fetching session info...');
        const info = await getSessionInfo();
        console.log('📊 Session info received:', info);
        setSessionInfo(info);
        
        // time_until_expiry가 유효한 숫자인지 확인
        const timeUntilExpiry = typeof info.time_until_expiry === 'number' ? info.time_until_expiry : 0;
        setTimeLeft(timeUntilExpiry);
        
        console.log(`🔍 Session analysis: is_active=${info.is_active}, time_until_expiry=${timeUntilExpiry}`);
        
        // 세션 상태 표시를 훨씬 더 보수적으로 처리
        if (!info.is_active && timeUntilExpiry <= 0) {
          console.log('❌ Session is definitely expired');
          setSessionStatus('expired');
          onSessionExpiry?.();
        } else if (timeUntilExpiry > 0 && timeUntilExpiry < 60) { // Only show warning if less than 1 minute left
          console.log('⚠️ Session expires very soon:', timeUntilExpiry);
          setSessionStatus('active');
          setIsVisible(true);
        } else {
          console.log('✅ Session is healthy, hiding indicator');
          setSessionStatus('active');
          setIsVisible(false);
        }
      } catch (error: any) {
        console.error('❌ Failed to fetch session info:', error);
        // Only show expired status for definitive authentication errors
        if (error?.response?.status === 401 || error?.response?.status === 403) {
          setSessionStatus('expired');
          setIsVisible(true);
        } else {
          // For other errors, just hide the indicator
          setIsVisible(false);
        }
      }
    };

    fetchSessionInfo();
    // Increase interval to reduce API calls - check every 2 minutes
    const interval = setInterval(fetchSessionInfo, 120000); 

    return () => clearInterval(interval);
  }, [onSessionExpiry]);

  // Countdown timer
  useEffect(() => {
    if (timeLeft <= 0) return;

    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          setSessionStatus('expired');
          onSessionExpiry?.();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft, onSessionExpiry]);

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getStatusConfig = () => {
    switch (sessionStatus) {
      case 'active':
        if (timeLeft < 300) {
          return {
            icon: AlertTriangle,
            color: 'text-yellow-600',
            bgColor: 'bg-yellow-50',
            borderColor: 'border-yellow-200',
            message: `세션 만료까지 ${formatTime(timeLeft)}`
          };
        }
        return {
          icon: CheckCircle,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          message: '세션 활성'
        };
      case 'expired':
        return {
          icon: AlertTriangle,
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          message: '세션이 만료되었습니다'
        };
      case 'renewed':
        return {
          icon: RefreshCw,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          message: '세션이 갱신되었습니다'
        };
      case 'reset':
        return {
          icon: RefreshCw,
          color: 'text-purple-600',
          bgColor: 'bg-purple-50',
          borderColor: 'border-purple-200',
          message: '대화가 초기화되었습니다'
        };
      default:
        return {
          icon: Clock,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          message: '세션 정보를 확인하는 중...'
        };
    }
  };

  const handleRenewSession = () => {
    setSessionStatus('renewed');
    onSessionRenewal?.();
    setTimeout(() => {
      setSessionStatus('active');
      setIsVisible(false);
    }, 3000);
  };

  // 임시로 세션 상태 표시기를 완전히 비활성화
  // 세션 관리는 백그라운드에서 정상적으로 작동하지만 UI 표시는 숨김
  return null;
  
  // if (!isVisible && sessionStatus === 'active') return null;

  const statusConfig = getStatusConfig();
  const IconComponent = statusConfig.icon;

  return (
    <AnimatePresence>
      <motion.div
        className={`flex items-center space-x-3 px-4 py-2 rounded-lg border ${statusConfig.bgColor} ${statusConfig.borderColor} ${className}`}
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.3 }}
      >
        <IconComponent className={`w-4 h-4 ${statusConfig.color}`} />
        <span className={`text-sm font-medium ${statusConfig.color}`}>
          {statusConfig.message}
        </span>
        
        {sessionStatus === 'expired' && (
          <motion.button
            className="text-sm bg-primary-600 text-white px-3 py-1 rounded-md hover:bg-primary-700 transition-colors"
            onClick={handleRenewSession}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            갱신
          </motion.button>
        )}
      </motion.div>
    </AnimatePresence>
  );
};

export default SessionStatusIndicator;