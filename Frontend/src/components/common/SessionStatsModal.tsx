import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Activity, MessageSquare, Clock, Users, TrendingUp } from 'lucide-react';
import { SessionStats } from '../../types';
import { getSessionStats } from '../../utils/api';

interface SessionStatsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SessionStatsModal = ({ isOpen, onClose }: SessionStatsModalProps) => {
  const [stats, setStats] = useState<SessionStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchStats();
    }
  }, [isOpen]);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const sessionStats = await getSessionStats();
      setStats(sessionStats);
    } catch (err) {
      console.error('Failed to fetch session stats:', err);
      setError('통계를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds}초`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}분`;
    return `${Math.floor(seconds / 3600)}시간 ${Math.floor((seconds % 3600) / 60)}분`;
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 px-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="bg-white rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto"
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-xl">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Activity className="w-6 h-6 text-blue-600" />
                  </div>
                  <h2 className="text-xl font-semibold text-gray-900">세션 통계</h2>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-3 text-gray-600">통계를 불러오는 중...</span>
                </div>
              ) : error ? (
                <div className="text-center py-12">
                  <div className="p-3 bg-red-100 rounded-full w-fit mx-auto mb-4">
                    <X className="w-6 h-6 text-red-600" />
                  </div>
                  <p className="text-red-600 mb-4">{error}</p>
                  <button
                    onClick={fetchStats}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    다시 시도
                  </button>
                </div>
              ) : stats ? (
                <div className="space-y-6">
                  {/* Overview Cards */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-xl">
                      <div className="flex items-center space-x-2 mb-2">
                        <Users className="w-4 h-4 text-blue-600" />
                        <span className="text-sm font-medium text-blue-800">전체 세션</span>
                      </div>
                      <div className="text-2xl font-bold text-blue-900">{stats.total_sessions}</div>
                    </div>

                    <div className="bg-gradient-to-br from-green-50 to-green-100 p-4 rounded-xl">
                      <div className="flex items-center space-x-2 mb-2">
                        <Activity className="w-4 h-4 text-green-600" />
                        <span className="text-sm font-medium text-green-800">활성 세션</span>
                      </div>
                      <div className="text-2xl font-bold text-green-900">{stats.active_sessions}</div>
                    </div>

                    <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-4 rounded-xl">
                      <div className="flex items-center space-x-2 mb-2">
                        <MessageSquare className="w-4 h-4 text-purple-600" />
                        <span className="text-sm font-medium text-purple-800">전체 메시지</span>
                      </div>
                      <div className="text-2xl font-bold text-purple-900">{stats.total_messages}</div>
                    </div>

                    <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-4 rounded-xl">
                      <div className="flex items-center space-x-2 mb-2">
                        <Clock className="w-4 h-4 text-orange-600" />
                        <span className="text-sm font-medium text-orange-800">평균 지속시간</span>
                      </div>
                      <div className="text-lg font-bold text-orange-900">
                        {formatDuration(stats.avg_session_duration)}
                      </div>
                    </div>
                  </div>

                  {/* Recent Activity */}
                  <div className="bg-gray-50 p-4 rounded-xl">
                    <div className="flex items-center space-x-2 mb-3">
                      <TrendingUp className="w-5 h-5 text-gray-600" />
                      <h3 className="font-semibold text-gray-800">최근 활동</h3>
                    </div>
                    <p className="text-gray-600">
                      {stats.most_recent_activity ? 
                        formatDate(stats.most_recent_activity) : 
                        '활동 기록이 없습니다.'
                      }
                    </p>
                  </div>

                  {/* Additional Info */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <strong>세션 활성율:</strong>{' '}
                      {stats.total_sessions > 0 
                        ? `${Math.round((stats.active_sessions / stats.total_sessions) * 100)}%`
                        : '0%'
                      }
                    </div>
                    <div className="bg-green-50 p-3 rounded-lg">
                      <strong>세션당 평균 메시지:</strong>{' '}
                      {stats.total_sessions > 0 
                        ? Math.round(stats.total_messages / stats.total_sessions)
                        : 0
                      }개
                    </div>
                  </div>
                </div>
              ) : null}
            </div>

            {/* Footer */}
            <div className="sticky bottom-0 bg-gray-50 px-6 py-4 rounded-b-xl border-t border-gray-200">
              <div className="flex justify-between items-center">
                <p className="text-sm text-gray-500">
                  세션은 30분 후 자동으로 만료됩니다
                </p>
                <button
                  onClick={onClose}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  닫기
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default SessionStatsModal;