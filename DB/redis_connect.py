import os
from dotenv import load_dotenv
import pickle  # json 대신 pickle 사용
import json
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

import redis


class RedisSessionManager:
    def __init__(self):
        try:
            load_dotenv()
            self.redis_host = os.getenv("REDIS_HOST")
            self.redis_port = int(os.getenv("REDIS_PORT", 6379)) # port는 정수형이어야 함
            self.redis_password = os.getenv("REDIS_PASSWORD")
            self.redis_db = int(os.getenv("REDIS_DB", 0)) # db는 정수형이어야 함
            self.redis_client = redis.Redis(
                host=self.redis_host, 
                port=self.redis_port, 
                password=self.redis_password, 
                db=self.redis_db,
                # pickle은 bytes로 작동하므로 decode_responses는 False여야 합니다.
                decode_responses=False 
            )
            # 연결 테스트
            self.redis_client.ping()
            print(f"✅ Redis connection successful: {self.redis_host}:{self.redis_port}/{self.redis_db}")
            
            # TTL 설정
            self.SHORT_TTL = 1800   # 30 minutes for active sessions
            self.LONG_TTL = 86400   # 24 hours for persistent data
            self.MAX_CHAT_HISTORY = 20  # Limit conversation length
            
        except Exception as e:
            print(f"Redis 연결 실패: {e}")
            raise e
    
    def save_session_state(self, session_id: str, state: Dict[str, Any], ttl_type: str = "short"):
        """세션 상태를 적절한 TTL로 저장합니다."""
        try:
            # 세션 ID를 문자열로 강제 변환 (int 입력 대비)
            session_id = str(session_id)
            ttl = self.SHORT_TTL if ttl_type == "short" else self.LONG_TTL
            
            # 대화 히스토리 제한
            if "chat_history" in state and len(state["chat_history"]) > self.MAX_CHAT_HISTORY:
                state["chat_history"] = state["chat_history"][-self.MAX_CHAT_HISTORY:]
            
            serialized_state = pickle.dumps(state)
            key = f"session:{session_id}"
            result = self.redis_client.set(key, serialized_state, ex=ttl)
            print(f"💾 Saved session {session_id[:8]}... to Redis (key={key}, ttl={ttl}s, result={result})")
            
            # 세션 메타데이터 저장
            metadata = {
                "last_activity": datetime.now().isoformat(),
                "conversation_count": len(state.get("chat_history", [])),
                "session_started": state.get("session_started", datetime.now().isoformat())
            }
            self.redis_client.set(f"session:meta:{session_id}", 
                                 json.dumps(metadata), ex=self.LONG_TTL)
                                 
        except Exception as e:
            print(f"세션 상태 저장 실패: {e}")
            raise e
    
    def save_state(self, session_id: str, state: Dict[str, Any]):
        """하위 호환성을 위한 기존 메소드"""
        self.save_session_state(session_id, state, "short")
    
    def load_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Redis에서 세션 상태를 불러와 pickle로 역직렬화합니다."""
        try:
            # 세션 ID를 문자열로 강제 변환 (int 입력 대비)
            session_id = str(session_id)
            # 새로운 키 형식 시도
            key = f"session:{session_id}"
            serialized_state = self.redis_client.get(key)
            print(f"🔍 Loading session {session_id[:8]}... from Redis (key={key}, found={serialized_state is not None})")
            
            # 없으면 기존 키 형식 시도 (하위 호환성)
            if serialized_state is None:
                old_key = f"state:{session_id}"
                serialized_state = self.redis_client.get(old_key)
                print(f"🔍 Tried old key format {old_key}, found={serialized_state is not None}")
            
            if serialized_state is None:
                # 키가 존재하는지 확인
                key_exists = self.redis_client.exists(key)
                ttl = self.redis_client.ttl(key)
                print(f"❌ Session not found: key_exists={key_exists}, ttl={ttl}")
                return None
            
            state = pickle.loads(serialized_state)
            print(f"✅ Successfully loaded session {session_id[:8]}... (size={len(str(state))} chars)")
            return state
        except (pickle.UnpicklingError, TypeError) as e:
            print(f"상태 불러오기 실패 (역직렬화 오류): {e}")
            return None
        except Exception as e:
            print(f"상태 불러오기 실패: {e}")
            raise e
    
    def get_session_metadata(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 메타데이터를 가져옵니다."""
        try:
            metadata = self.redis_client.get(f"session:meta:{session_id}")
            if metadata:
                return json.loads(metadata)
            return None
        except Exception as e:
            print(f"메타데이터 불러오기 실패: {e}")
            return None
    
    def update_session_activity(self, session_id: str):
        """세션 활동을 업데이트하고 TTL을 갱신합니다."""
        try:
            # 세션 TTL 갱신
            self.redis_client.expire(f"session:{session_id}", self.SHORT_TTL)
            
            # 활동 시간 업데이트
            activity_data = {
                "last_activity": datetime.now().isoformat(),
                "activity_count": self.get_activity_count(session_id) + 1
            }
            self.redis_client.set(f"session:activity:{session_id}", 
                                 json.dumps(activity_data), ex=self.LONG_TTL)
        except Exception as e:
            print(f"세션 활동 업데이트 실패: {e}")
    
    def get_activity_count(self, session_id: str) -> int:
        """세션의 활동 횟수를 가져옵니다."""
        try:
            activity_data = self.redis_client.get(f"session:activity:{session_id}")
            if activity_data:
                data = json.loads(activity_data)
                return data.get("activity_count", 0)
            return 0
        except Exception:
            return 0
    
    def should_renew_session(self, session_id: str) -> bool:
        """세션을 갱신해야 하는지 확인합니다."""
        try:
            # Check if the main session key exists
            session_exists = self.redis_client.exists(f"session:{session_id}")
            if not session_exists:
                return True
                
            # Check TTL - if less than 2 minutes remaining, suggest renewal
            ttl = self.redis_client.ttl(f"session:{session_id}")
            if ttl < 120:  # Less than 2 minutes (more conservative)
                return True
                
            metadata = self.get_session_metadata(session_id)
            if not metadata:
                return False  # Session exists but no metadata, don't force renewal
                
            last_activity = datetime.fromisoformat(metadata["last_activity"])
            # Only suggest renewal if session has been inactive for more than 28 minutes (more conservative)
            inactive_seconds = (datetime.now() - last_activity).total_seconds()
            return inactive_seconds > (self.SHORT_TTL - 120)  # 28 minutes
        except Exception as e:
            print(f"Error checking session renewal: {e}")
            return False  # Don't force renewal on errors
    
    def create_conversation_thread(self, session_id: str, thread_id: str = None) -> str:
        """세션 내에 새로운 대화 스레드를 생성합니다."""
        if not thread_id:
            thread_id = str(uuid.uuid4())[:8]
            
        thread_key = f"session:{session_id}:thread:{thread_id}"
        
        thread_data = {
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "message_count": 0
        }
        
        self.redis_client.set(f"{thread_key}:meta", json.dumps(thread_data), ex=self.SHORT_TTL)
        return thread_id
    
    def get_active_thread(self, session_id: str) -> str:
        """활성 대화 스레드를 가져오거나 생성합니다."""
        active_thread_key = f"session:{session_id}:active_thread"
        thread_id = self.redis_client.get(active_thread_key)
        
        if not thread_id:
            thread_id = self.create_conversation_thread(session_id)
            self.redis_client.set(active_thread_key, thread_id, ex=self.SHORT_TTL)
        
        return thread_id.decode() if isinstance(thread_id, bytes) else thread_id
    
    def get_state_size(self, session_id: str) -> int:
        """세션 상태의 크기를 바이트 단위로 반환합니다."""
        try:
            serialized_state = self.redis_client.get(f"session:{session_id}")
            if serialized_state:
                return len(serialized_state)
            return 0
        except Exception:
            return 0
    
    def cleanup_expired_sessions(self):
        """만료된 세션을 정리합니다."""
        try:
            pattern = "session:*"
            for key in self.redis_client.scan_iter(match=pattern):
                ttl = self.redis_client.ttl(key)
                if ttl < 300:  # 5분 미만 남은 세션
                    print(f"정리할 세션: {key.decode() if isinstance(key, bytes) else key}")
        except Exception as e:
            print(f"세션 정리 실패: {e}")
    
    # save_chat_history_json 함수는 더 이상 필요 없으므로 삭제합니다.

# 하위 호환성을 위한 별칭
RedisConnect = RedisSessionManager

if __name__ == "__main__":
    rc = RedisSessionManager()
    session_id = "10"  # 저장할 때 쓴 세션 ID (예: WorkFlow/main.py에서 user_id=10)
    state = rc.load_state(session_id)
    print(state)