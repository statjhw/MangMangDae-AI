import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, CheckCircle, RotateCcw, MessageSquare, Brain, Clock } from 'lucide-react';
import { ContextResetEvent, ResetReason } from '../../types';

interface ContextResetNotificationProps {
  resetEvents: ContextResetEvent[];
  onDismiss?: (eventId: string) => void;
}

const ContextResetNotification = ({ 
  resetEvents, 
  onDismiss 
}: ContextResetNotificationProps) => {
  const [visibleEvents, setVisibleEvents] = useState<ContextResetEvent[]>([]);

  useEffect(() => {
    // Show new events
    const newEvents = resetEvents.filter(event => 
      !visibleEvents.some(visible => 
        visible.timestamp.getTime() === event.timestamp.getTime()
      )
    );

    if (newEvents.length > 0) {
      setVisibleEvents(prev => [...prev, ...newEvents]);
      
      // Auto-dismiss after 8 seconds for non-manual resets
      newEvents.forEach(event => {
        if (event.reason !== 'manual') {
          setTimeout(() => {
            setVisibleEvents(prev => 
              prev.filter(e => e.timestamp.getTime() !== event.timestamp.getTime())
            );
          }, 8000);
        }
      });
    }
  }, [resetEvents, visibleEvents]);

  const getEventConfig = (reason: ResetReason) => {
    switch (reason) {
      case 'manual':
        return {
          icon: RotateCcw,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          title: '수동 초기화',
          description: '사용자가 대화를 초기화했습니다.'
        };
      case 'message_limit':
        return {
          icon: MessageSquare,
          color: 'text-orange-600',
          bgColor: 'bg-orange-50',
          borderColor: 'border-orange-200',
          title: '메시지 한도 도달',
          description: '대화가 길어져서 자동으로 초기화되었습니다.'
        };
      case 'topic_shift':
        return {
          icon: Brain,
          color: 'text-purple-600',
          bgColor: 'bg-purple-50',
          borderColor: 'border-purple-200',
          title: '주제 변경 감지',
          description: '대화 주제가 바뀌어서 초기화되었습니다.'
        };
      case 'reset_phrase':
        return {
          icon: CheckCircle,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          title: '새로운 질문',
          description: '초기화 키워드를 감지했습니다.'
        };
      case 'session_renewal':
        return {
          icon: Clock,
          color: 'text-indigo-600',
          bgColor: 'bg-indigo-50',
          borderColor: 'border-indigo-200',
          title: '세션 갱신',
          description: '세션이 갱신되어 대화를 초기화했습니다.'
        };
      default:
        return {
          icon: AlertCircle,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          title: '대화 초기화',
          description: '대화가 초기화되었습니다.'
        };
    }
  };

  const handleDismiss = (event: ContextResetEvent) => {
    const eventId = event.timestamp.getTime().toString();
    setVisibleEvents(prev => 
      prev.filter(e => e.timestamp.getTime() !== event.timestamp.getTime())
    );
    onDismiss?.(eventId);
  };

  if (visibleEvents.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
      <AnimatePresence>
        {visibleEvents.slice(-3).map((event) => { // Show only last 3 events
          const config = getEventConfig(event.reason);
          const IconComponent = config.icon;
          
          return (
            <motion.div
              key={event.timestamp.getTime()}
              initial={{ opacity: 0, x: 300, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 300, scale: 0.95 }}
              transition={{ duration: 0.4, type: "spring", stiffness: 120 }}
              className={`p-4 rounded-xl border shadow-lg backdrop-blur-sm bg-white/95 ${config.borderColor}`}
            >
              <div className="flex items-start space-x-3">
                <div className={`p-2 rounded-full ${config.bgColor} flex-shrink-0`}>
                  <IconComponent className={`w-5 h-5 ${config.color}`} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className={`text-sm font-semibold ${config.color}`}>
                      {config.title}
                    </h4>
                    <button
                      onClick={() => handleDismiss(event)}
                      className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-2">
                    {event.message || config.description}
                  </p>
                  
                  <div className="text-xs text-gray-400">
                    {event.timestamp.toLocaleTimeString('ko-KR', { 
                      hour: '2-digit', 
                      minute: '2-digit', 
                      second: '2-digit' 
                    })}
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
};

export default ContextResetNotification;