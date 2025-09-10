import { useState, useRef, useEffect, FormEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, User, Loader2, Send, Sparkles, RotateCcw, Info, TrendingUp, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import rehypeRaw from 'rehype-raw';
import { UserInfo, ChatMessage, UserStatResponse } from '../../types';
import { runWorkflow, resetConversation, getUserStat } from '../../utils/api';
import UserStatSection from './UserStatSection';
import toast from 'react-hot-toast';

const cn = (...classes: (string | boolean | undefined)[]) => classes.filter(Boolean).join(' ');

interface ChatSectionProps {
  userInfo: UserInfo;
}

const ChatSection = ({ userInfo }: ChatSectionProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isResetModalOpen, setIsResetModalOpen] = useState(false);
  const [isStatsModalOpen, setIsStatsModalOpen] = useState(false);
  const [userStat, setUserStat] = useState<UserStatResponse | null>(null);
  const [statLoading, setStatLoading] = useState(false);
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

  // 단순화된 대화 초기화 처리
  
  const handleManualReset = async () => {
    try {
      setIsLoading(true);
      await resetConversation();
      
      // 단순한 성공 메시지
      const systemMessage: ChatMessage = {
        id: `system-reset-${Date.now()}`,
        role: 'assistant',
        content: '🔄 대화를 새로 시작합니다. 이전 대화 내용은 초기화되었습니다.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, systemMessage]);
      
      toast.success('대화가 초기화되었습니다');
      setIsResetModalOpen(false);
    } catch (error: any) {
      console.error('Failed to reset conversation:', error);
      toast.error('대화 초기화에 실패했습니다. 페이지를 새로고침해주세요.');
      setIsResetModalOpen(false);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle stats modal
  const handleShowStats = async () => {
    if (!userStat) {
      setStatLoading(true);
      try {
        const statData = await getUserStat(userInfo);
        setUserStat(statData);
      } catch (error) {
        console.error('Failed to fetch user statistics:', error);
        toast.error('통계 데이터를 가져오는데 실패했습니다.');
        return;
      } finally {
        setStatLoading(false);
      }
    }
    setIsStatsModalOpen(true);
  };
  
  // 복잡한 세션 이벤트 리스너들 제거됨

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
    <motion.section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-secondary-800 mb-4">AI 커리어 상담</h2>
        <p className="text-lg text-secondary-600">AI 어드바이저와 자유롭게 대화하며 궁금증을 해결하세요.</p>
      </div>
      
      {/* 단순화된 컨트롤 버튼들 */}
      <div className="flex justify-center items-center gap-3 mb-8">
        {/* 나의 정보 통계 보기 버튼 */}
        <motion.button
          onClick={handleShowStats}
          disabled={isLoading || statLoading}
          className="flex items-center justify-center space-x-2 px-4 py-2.5 bg-primary-600 hover:bg-primary-700 focus:ring-4 focus:ring-primary-200 text-white rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md text-sm sm:text-base"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          aria-label={statLoading ? "통계 데이터 로딩 중" : "나의 정보 통계 보기"}
        >
          {statLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="font-medium">로딩중...</span>
            </>
          ) : (
            <>
              <TrendingUp className="w-4 h-4" />
              <span className="font-medium hidden sm:inline">나의 정보 통계 보기</span>
              <span className="font-medium sm:hidden">통계 보기</span>
            </>
          )}
        </motion.button>
        
        <motion.button
          onClick={() => setIsResetModalOpen(true)}
          disabled={isLoading}
          className="flex items-center justify-center space-x-2 px-4 py-2.5 bg-gray-100 hover:bg-gray-200 focus:ring-4 focus:ring-gray-200 text-gray-700 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md text-sm sm:text-base"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          aria-label="대화 초기화"
        >
          <RotateCcw className="w-4 h-4" />
          <span className="font-medium hidden sm:inline">대화 초기화</span>
          <span className="font-medium sm:hidden">초기화</span>
        </motion.button>
      </div>

      <div className="bg-white rounded-xl shadow-lg border border-secondary-200 flex flex-col h-[75vh] sm:h-[80vh]">
        <div className="flex-1 p-3 sm:p-6 space-y-4 sm:space-y-6 overflow-y-auto">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div key={message.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className={cn('flex items-start gap-2 sm:gap-4', message.role === 'user' ? 'justify-end' : 'justify-start')}>
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-primary-600 to-primary-700 rounded-full flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 sm:w-6 sm:h-6 text-white" />
                  </div>
                )}
                <div className={cn('max-w-[85%] sm:max-w-md lg:max-w-lg p-3 sm:p-4 rounded-2xl text-sm sm:text-base', message.role === 'user' ? 'bg-primary-600 text-white rounded-br-none' : 'bg-secondary-100 text-secondary-800 rounded-bl-none')}>
                  {message.role === 'user' ? (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  ) : (
                    <ReactMarkdown
                      className="prose prose-sm max-w-none prose-headings:text-secondary-800 prose-p:text-secondary-700 prose-strong:text-secondary-800 prose-em:text-secondary-700 prose-code:bg-secondary-200 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-secondary-800 prose-pre:bg-secondary-200 prose-pre:text-secondary-800 prose-ul:text-secondary-700 prose-ol:text-secondary-700 prose-li:text-secondary-700"
                      remarkPlugins={[remarkGfm, remarkBreaks]}
                      rehypePlugins={[rehypeRaw]}
                      components={{
                        h1: ({ children }) => (
                          <div className="bg-gradient-to-r from-primary-50 to-blue-50 p-3 rounded-lg mb-3 border-l-4 border-primary-500">
                            <h1 className="text-lg font-bold text-primary-800 flex items-start gap-2">
                              <span className="flex-shrink-0">🏢</span> 
                              <span className="break-words">{children}</span>
                            </h1>
                          </div>
                        ),
                        h2: ({ children }) => {
                          const childrenText = String(children);
                          const companyMatch = childrenText.match(/^(\d+)\.\s*(.+?)(?:\s*위치:|$)/);
                          
                          if (companyMatch) {
                            const [, number, companyName] = companyMatch;
                            return (
                              <div className="bg-white p-4 rounded-lg mb-3 border border-secondary-200 shadow-sm">
                                <div className="flex items-start gap-3">
                                  <span className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center text-sm font-bold text-primary-600 flex-shrink-0">
                                    {number}
                                  </span>
                                  <div className="flex-1 min-w-0">
                                    <h2 className="text-base font-semibold text-secondary-800 break-words leading-tight">
                                      {companyName.trim()}
                                    </h2>
                                  </div>
                                </div>
                              </div>
                            );
                          }
                          
                          return (
                            <div className="bg-white p-3 rounded-lg mb-3 border border-secondary-200 shadow-sm">
                              <h2 className="text-base font-semibold text-secondary-800 flex items-start gap-2">
                                <span className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center text-xs font-bold text-primary-600 flex-shrink-0">
                                  {childrenText.match(/^\d+/) || '•'}
                                </span>
                                <span className="break-words">{children}</span>
                              </h2>
                            </div>
                          );
                        },
                        h3: ({ children }) => (
                          <h3 className="text-base font-medium text-secondary-800 mb-2 flex items-center gap-2">
                            <span className="text-primary-500">▶</span>
                            {children}
                          </h3>
                        ),
                        p: ({ children }) => <p className="text-secondary-700 mb-3 leading-relaxed last:mb-0">{children}</p>,
                        ul: ({ children }) => <ul className="space-y-2 mb-3">{children}</ul>,
                        ol: ({ children }) => <ol className="space-y-2 mb-3">{children}</ol>,
                        li: ({ children }) => {
                          const content = String(children);
                          // 특정 패턴들을 감지해서 아이콘 추가
                          let icon = '•';
                          if (content.includes('위치') || content.includes('📍')) icon = '📍';
                          else if (content.includes('연봉') || content.includes('💰')) icon = '💰';
                          else if (content.includes('직무') || content.includes('💼')) icon = '💼';
                          else if (content.includes('추천') || content.includes('🎯')) icon = '🎯';
                          else if (content.includes('특징') || content.includes('✨')) icon = '✨';
                          else if (content.includes('매칭') || content.includes('⭐')) icon = '⭐';
                          
                          return (
                            <li className="flex items-start gap-2 text-secondary-700 bg-secondary-50 p-2 rounded-md">
                              <span className="text-sm mt-0.5 flex-shrink-0">{icon}</span>
                              <span>{children}</span>
                            </li>
                          );
                        },
                        strong: ({ children }) => <strong className="font-semibold text-primary-700 bg-primary-50 px-1 rounded">{children}</strong>,
                        em: ({ children }) => <em className="italic text-secondary-600">{children}</em>,
                        code: ({ children }) => <code className="bg-gray-100 px-2 py-1 rounded text-sm text-gray-800 font-mono">{children}</code>,
                        pre: ({ children }) => <pre className="bg-gray-100 p-3 rounded-lg text-sm text-gray-800 overflow-x-auto mb-3">{children}</pre>,
                        blockquote: ({ children }) => (
                          <blockquote className="border-l-4 border-amber-300 bg-amber-50 pl-4 pr-3 py-2 text-amber-800 italic mb-3 rounded-r-lg">
                            <div className="flex items-start gap-2">
                              <span className="text-lg">💡</span>
                              <div>{children}</div>
                            </div>
                          </blockquote>
                        ),
                        hr: () => (
                          <div className="my-4 flex items-center">
                            <div className="flex-1 border-t-2 border-dotted border-secondary-300"></div>
                            <div className="px-3 text-secondary-400">✦</div>
                            <div className="flex-1 border-t-2 border-dotted border-secondary-300"></div>
                          </div>
                        )
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  )}
                </div>
                {message.role === 'user' && (
                  <div className="w-8 h-8 sm:w-10 sm:h-10 bg-secondary-200 rounded-full flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 sm:w-6 sm:h-6 text-secondary-600" />
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
          {isLoading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-start gap-2 sm:gap-4 justify-start">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-primary-600 to-primary-700 rounded-full flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 sm:w-6 sm:h-6 text-white" />
              </div>
              <div className="bg-secondary-100 text-secondary-800 p-3 sm:p-4 rounded-2xl rounded-bl-none max-w-[85%] sm:max-w-md lg:max-w-lg">
                <div className="flex items-center space-x-2 sm:space-x-3 mb-2 sm:mb-3">
                  <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 text-primary-600 animate-spin flex-shrink-0" />
                  <span className="text-xs sm:text-sm font-medium text-secondary-700">AI가 답변을 생성하고 있습니다...</span>
                </div>
                <div className="bg-primary-50 border border-primary-200 rounded-lg p-2 sm:p-3 text-xs sm:text-sm">
                  <div className="flex items-center space-x-2 mb-1 sm:mb-2">
                    <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse"></div>
                    <span className="text-primary-700 font-medium">예상 소요 시간: 1-2분</span>
                  </div>
                  <p className="text-primary-600 text-xs">
                    복잡한 분석을 위해 다소 시간이 소요될 수 있습니다. 잠시만 기다려 주세요.
                  </p>
                </div>
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <div className="border-t border-secondary-200 bg-secondary-50 p-3 sm:p-4 rounded-b-xl">
          <form onSubmit={handleSendMessage} className="flex items-center gap-2 sm:gap-4">
            <div className="flex-1 relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={isLoading ? "AI가 답변을 생성하고 있습니다... (1-2분 소요)" : "추가 질문을 입력하세요... (대화 초기화: '새로운 질문', '처음부터')"}
                className="w-full pl-3 sm:pl-4 pr-10 sm:pr-12 py-2.5 sm:py-3 rounded-lg border-secondary-300 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all duration-200 text-sm sm:text-base disabled:bg-gray-50 disabled:text-gray-500"
                disabled={isLoading}
                aria-label="메시지 입력"
              />
              <div className="absolute inset-y-0 right-0 flex items-center pr-2 sm:pr-3">
                <Sparkles className="w-4 h-4 sm:w-5 sm:h-5 text-secondary-400" />
              </div>
            </div>
            <motion.button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-4 sm:px-6 py-2.5 sm:py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 focus:ring-2 focus:ring-primary-200 disabled:bg-primary-300 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center shadow-sm hover:shadow-md"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              aria-label={isLoading ? "메시지 전송 중" : "메시지 전송"}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" />
              ) : (
                <Send className="w-4 h-4 sm:w-5 sm:h-5" />
              )}
            </motion.button>
          </form>
        </div>
      </div>
      
      {/* 복잡한 컨텍스트 리셋 알림 제거됨 */}
      
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
      
      {/* 나의 정보 통계 모달 */}
      <AnimatePresence>
        {isStatsModalOpen && (
          <motion.div
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 px-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsStatsModalOpen(false)}
          >
            <motion.div
              className="bg-white rounded-xl max-w-6xl max-h-[90vh] w-full overflow-y-auto"
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">나의 정보 통계</h2>
                <button
                  onClick={() => setIsStatsModalOpen(false)}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>
              
              <div className="p-0">
                <UserStatSection userStat={userStat} loading={statLoading} />
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.section>
  );
};

export default ChatSection; 