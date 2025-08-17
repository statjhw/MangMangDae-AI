import { useState, useRef, useEffect, FormEvent, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, User, Loader2, Send, Sparkles, RotateCcw, Info } from 'lucide-react';
import { UserInfo, ChatMessage, ContextResetEvent, ResetReason } from '../../types';
import { runWorkflow, resetConversation } from '../../utils/api';
import SessionStatusIndicator from '../common/SessionStatusIndicator';
import ContextResetNotification from '../common/ContextResetNotification';
import toast from 'react-hot-toast';

const cn = (...classes: (string | boolean | undefined)[]) => classes.filter(Boolean).join(' ');

interface ChatSectionProps {
  userInfo: UserInfo;
}

const ChatSection = ({ userInfo }: ChatSectionProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [contextResetEvents, setContextResetEvents] = useState<ContextResetEvent[]>([]);
  const [isResetModalOpen, setIsResetModalOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const analysisStarted = useRef(false);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);
  

  useEffect(() => {
    if (analysisStarted.current) return;
    analysisStarted.current = true;

    const handleInitialAnalysis = async () => {
      setIsLoading(true);
      setMessages([{
        id: `user-${Date.now()}`,
        role: 'user',
        content: userInfo.candidate_question,
        timestamp: new Date(),
      }]);

      try {
        const result = await runWorkflow(userInfo);
        setMessages((prev) => [...prev, {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: result.final_answer,
          timestamp: new Date(),
        }]);
        toast.success('AI 분석이 완료되었습니다!');
      } catch (error: any) {
        console.error('Failed to get initial response:', error);
        
        let errorMessage = '죄송합니다. 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
        
        if (error.response?.status === 429) {
          errorMessage = '🚀 요청이 너무 많습니다. 잠시 후 다시 시도해주세요.';
        } else if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
          errorMessage = '⏱️ 분석 시간이 너무 오래 걸리고 있습니다. 잠시 후 다시 시도해주세요.';
        }
        
        setMessages((prev) => [...prev, {
          id: `assistant-error-${Date.now()}`,
          role: 'assistant',
          content: errorMessage,
          timestamp: new Date(),
        }]);
        toast.error('분석 중 오류가 발생했습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    if (userInfo.candidate_question) {
      handleInitialAnalysis();
    }
  }, [userInfo]);

  // Handle context reset events
  const handleContextReset = useCallback((reason: ResetReason, customMessage?: string) => {
    const resetEvent: ContextResetEvent = {
      reason,
      timestamp: new Date(),
      message: customMessage
    };
    
    setContextResetEvents(prev => [...prev, resetEvent]);
    
    // Add system message to chat
    const systemMessage: ChatMessage = {
      id: `system-reset-${Date.now()}`,
      role: 'assistant',
      content: getResetMessage(reason, customMessage),
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, systemMessage]);
    
    // Show toast notification
    toast.success(getResetToastMessage(reason));
  }, []);
  
  const getResetMessage = (reason: ResetReason, customMessage?: string): string => {
    if (customMessage) return customMessage;
    
    switch (reason) {
      case 'manual':
        return '🔄 대화를 새로 시작합니다. 이전 대화 내용은 초기화되었습니다.';
      case 'message_limit':
        return '📝 대화가 길어져서 새로 시작합니다. 더 정확한 답변을 위해 이전 내용을 정리했습니다.';
      case 'topic_shift':
        return '💡 새로운 주제로 전환되었습니다. 더 나은 답변을 위해 대화를 새로 시작합니다.';
      case 'reset_phrase':
        return '🆕 새로운 질문으로 시작합니다!';
      case 'session_renewal':
        return '🔄 세션이 갱신되어 대화를 새로 시작합니다.';
      default:
        return '🔄 대화가 초기화되었습니다.';
    }
  };
  
  const getResetToastMessage = (reason: ResetReason): string => {
    switch (reason) {
      case 'manual':
        return '대화가 초기화되었습니다';
      case 'message_limit':
        return '대화 길이로 인해 자동 초기화되었습니다';
      case 'topic_shift':
        return '주제 변경으로 대화가 초기화되었습니다';
      case 'reset_phrase':
        return '새로운 질문으로 시작합니다';
      case 'session_renewal':
        return '세션 갱신으로 대화가 초기화되었습니다';
      default:
        return '대화가 초기화되었습니다';
    }
  };
  
  const handleManualReset = async () => {
    try {
      setIsLoading(true);
      await resetConversation();
      handleContextReset('manual');
      setIsResetModalOpen(false);
    } catch (error: any) {
      console.error('Failed to reset conversation:', error);
      
      let errorMessage = '대화 초기화 중 오류가 발생했습니다';
      
      if (error.response?.status === 401 || error.response?.status === 403) {
        errorMessage = '세션 만료로 인해 초기화에 실패했습니다. 페이지를 새로고침해주세요.';
      } else if (error.response?.status === 429) {
        errorMessage = '요청이 너무 많습니다. 잠시 후 다시 시도해주세요.';
      } else if (!error.response) {
        errorMessage = '네트워크 연결을 확인해주세요.';
      }
      
      toast.error(errorMessage);
      
      // Close modal anyway on certain errors
      if (error.response?.status === 401 || error.response?.status === 403) {
        setIsResetModalOpen(false);
      }
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSessionExpiry = useCallback(() => {
    // Silently handle session expiry without showing disruptive messages
    console.log('Session expired - handled silently');
  }, []);
  
  const handleSessionRenewal = useCallback(() => {
    // Handle session renewal silently without disrupting user experience
    console.log('Session renewal handled silently');
  }, []);
  
  // Listen for global session events
  useEffect(() => {
    const handleSessionRenewedEvent = (event: CustomEvent) => {
      console.log('Session renewal event:', event.detail);
      // Handle session renewal silently - no need to show user disruptive messages for background session management
    };
    
    const handleSessionExpiredEvent = (event: CustomEvent) => {
      console.log('Session expiry event:', event.detail);
      // Handle session expiry silently without showing disruptive messages to user
      // Only log for debugging purposes
    };
    
    window.addEventListener('sessionRenewed', handleSessionRenewedEvent as EventListener);
    window.addEventListener('sessionExpired', handleSessionExpiredEvent as EventListener);
    
    return () => {
      window.removeEventListener('sessionRenewed', handleSessionRenewedEvent as EventListener);
      window.removeEventListener('sessionExpired', handleSessionExpiredEvent as EventListener);
    };
  }, [handleContextReset]);

  const handleSendMessage = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`, role: 'user', content: input, timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);

    try {
      const workflowInput = { ...userInfo, candidate_question: currentInput };
      const result = await runWorkflow(workflowInput);
      
      // Check if backend indicates a context reset in response
      if (result.final_answer.includes('새로운 질문') || 
          result.final_answer.includes('처음부터') ||
          result.final_answer.includes('대화를 새로')) {
        handleContextReset('reset_phrase');
      }
      
      setMessages((prev) => [...prev, {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: result.final_answer,
        timestamp: new Date(),
      }]);
    } catch (error: any) {
      console.error('Failed to send message:', error);
      
      let errorMessage = '죄송합니다. 답변을 처리하는 중 오류가 발생했습니다.';
      let toastMessage = '메시지 전송 중 오류 발생';
      
      // Handle different types of errors
      if (error.response?.status === 401 || error.response?.status === 403) {
        errorMessage = '⏰ 세션이 만료되었습니다. 잠시 후 다시 시도해주세요.';
        toastMessage = '세션 만료로 인해 요청에 실패했습니다';
        // Don't manually trigger handleSessionExpiry here as the interceptor will handle it
      } else if (error.response?.status === 429) {
        errorMessage = '🚀 요청이 너무 많습니다. 잠시 후 다시 시도해주세요.';
        toastMessage = '요청 제한에 도달했습니다';
      } else if (error.response?.status === 500) {
        errorMessage = '😱 서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
        toastMessage = '서버 오류가 발생했습니다';
      } else if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        errorMessage = '⏱️ 요청 시간이 초과되었습니다. 네트워크 연결을 확인해주세요.';
        toastMessage = '요청 시간 초과';
      } else if (!error.response) {
        errorMessage = '🌐 네트워크 연결을 확인해주세요.';
        toastMessage = '네트워크 연결 오류';
      }
      
      setMessages((prev) => [...prev, {
        id: `assistant-error-${Date.now()}`,
        role: 'assistant',
        content: errorMessage,
        timestamp: new Date(),
      }]);
      
      toast.error(toastMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-secondary-800 mb-4">AI 커리어 상담</h2>
        <p className="text-lg text-secondary-600">AI 어드바이저와 자유롭게 대화하며 궁금증을 해결하세요.</p>
      </div>
      
      {/* Session Status and Controls */}
      <div className="flex justify-center items-center space-x-4 mb-8">
        <SessionStatusIndicator 
          onSessionExpiry={handleSessionExpiry}
          onSessionRenewal={handleSessionRenewal}
        />
        <button
          onClick={() => setIsResetModalOpen(true)}
          disabled={isLoading}
          className="flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RotateCcw className="w-4 h-4" />
          <span className="text-sm font-medium">대화 초기화</span>
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-lg border border-secondary-200 flex flex-col h-[80vh]">
        <div className="flex-1 p-6 space-y-6 overflow-y-auto">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div key={message.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className={cn('flex items-start gap-4', message.role === 'user' ? 'justify-end' : 'justify-start')}>
                {message.role === 'assistant' && (
                  <div className="w-10 h-10 bg-gradient-to-br from-primary-600 to-primary-700 rounded-full flex items-center justify-center flex-shrink-0">
                    <Bot className="w-6 h-6 text-white" />
                  </div>
                )}
                <div className={cn('max-w-md lg:max-w-lg p-4 rounded-2xl', message.role === 'user' ? 'bg-primary-600 text-white rounded-br-none' : 'bg-secondary-100 text-secondary-800 rounded-bl-none')}>
                  {/* 마크다운 렌더링을 제거하고, 줄바꿈이 유지되는 일반 텍스트로 표시 */}
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>
                {message.role === 'user' && (
                  <div className="w-10 h-10 bg-secondary-200 rounded-full flex items-center justify-center flex-shrink-0">
                    <User className="w-6 h-6 text-secondary-600" />
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
          {isLoading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-start gap-4 justify-start">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-600 to-primary-700 rounded-full flex items-center justify-center flex-shrink-0">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div className="bg-secondary-100 text-secondary-800 p-4 rounded-2xl rounded-bl-none">
                <Loader2 className="w-6 h-6 text-primary-600 animate-spin" />
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <div className="border-t border-secondary-200 bg-secondary-50 p-4 rounded-b-xl">
          <form onSubmit={handleSendMessage} className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={isLoading ? "AI가 분석 중입니다..." : "추가 질문을 입력하세요... (초기화: '새로운 질문', '처음부터')"}
                className="w-full pl-4 pr-12 py-3 rounded-lg border-secondary-300 focus:ring-primary-500 focus:border-primary-500 transition"
                disabled={isLoading}
              />
              <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                <Sparkles className="w-5 h-5 text-secondary-400" />
              </div>
            </div>
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-6 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 disabled:bg-primary-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </form>
        </div>
      </div>
      
      {/* Context Reset Notifications */}
      <ContextResetNotification 
        resetEvents={contextResetEvents}
        onDismiss={(eventId) => {
          setContextResetEvents(prev => 
            prev.filter(event => event.timestamp.getTime().toString() !== eventId)
          );
        }}
      />
      
      {/* Reset Confirmation Modal */}
      <AnimatePresence>
        {isResetModalOpen && (
          <motion.div
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 px-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsResetModalOpen(false)}
          >
            <motion.div
              className="bg-white rounded-xl p-6 max-w-md w-full"
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 bg-orange-100 rounded-full">
                  <Info className="w-6 h-6 text-orange-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">대화 초기화</h3>
              </div>
              
              <p className="text-gray-600 mb-6">
                현재 대화 내용이 모두 삭제되고 새로운 대화를 시작합니다. 계속하시겠습니까?
              </p>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => setIsResetModalOpen(false)}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  취소
                </button>
                <button
                  onClick={handleManualReset}
                  disabled={isLoading}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-red-400 disabled:cursor-not-allowed transition-colors"
                >
                  {isLoading ? '초기화 중...' : '초기화'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.section>
  );
};

export default ChatSection; 