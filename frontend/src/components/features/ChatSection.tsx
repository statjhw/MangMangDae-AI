import { useState, useRef, useEffect, FormEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, User, Loader2, Send, Sparkles } from 'lucide-react';
import { UserInfo, ChatMessage } from '../../types';
import { runWorkflow } from '../../utils/api';
import toast from 'react-hot-toast';

const cn = (...classes: (string | boolean | undefined)[]) => classes.filter(Boolean).join(' ');

interface ChatSectionProps {
  userInfo: UserInfo;
}

const ChatSection = ({ userInfo }: ChatSectionProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(true);
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
      } catch (error) {
        console.error('Failed to get initial response:', error);
        setMessages((prev) => [...prev, {
          id: `assistant-error-${Date.now()}`,
          role: 'assistant',
          content: '죄송합니다. 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
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
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages((prev) => [...prev, {
        id: `assistant-error-${Date.now()}`,
        role: 'assistant',
        content: '죄송합니다. 답변을 처리하는 중 오류가 발생했습니다.',
        timestamp: new Date(),
      }]);
      toast.error('메시지 전송 중 오류 발생');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-secondary-800 mb-4">AI 커리어 상담</h2>
        <p className="text-lg text-secondary-600">AI 어드바이저와 자유롭게 대화하며 궁금증을 해결하세요.</p>
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
                placeholder={isLoading ? "AI가 분석 중입니다..." : "추가 질문을 입력하세요..."}
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
    </motion.section>
  );
};

export default ChatSection; 