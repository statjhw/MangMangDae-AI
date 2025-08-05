import os
from dotenv import load_dotenv
import pickle  # json 대신 pickle 사용
from typing import Dict, Any, Optional

import redis

class RedisConnect:
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
        except Exception as e:
            print(f"Redis 연결 실패: {e}")
            raise e
    
    def save_state(self, session_id: str, state: Dict[str, Any]):
        """대화 상태를 pickle로 직렬화하여 Redis에 저장합니다."""
        try:
            serialized_state = pickle.dumps(state)
            # 키에 접두사를 사용하고, 만료시간(TTL)을 24시간으로 설정합니다.
            self.redis_client.set(f"state:{session_id}", serialized_state, ex=86400)
        except Exception as e:
            print(f"상태 저장 실패: {e}")
            raise e
    
    def load_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Redis에서 대화 상태를 불러와 pickle로 역직렬화합니다."""
        try:
            serialized_state = self.redis_client.get(f"state:{session_id}")
            
            if serialized_state is None:
                return None
            
            return pickle.loads(serialized_state)
        except (pickle.UnpicklingError, TypeError) as e:
            print(f"상태 불러오기 실패 (역직렬화 오류): {e}")
            return None
        except Exception as e:
            print(f"상태 불러오기 실패: {e}")
            raise e
    
    # save_chat_history_json 함수는 더 이상 필요 없으므로 삭제합니다.

if __name__ == "__main__":
    redis_connect = RedisConnect()
    print("Redis PING:", redis_connect.redis_client.ping())

    # 간단한 테스트
    test_session_id = "test-session-123"
    test_state = {"message": "hello"}
    redis_connect.save_state(test_session_id, test_state)
    loaded = redis_connect.load_state(test_session_id)
    print(f"Saved and loaded state: {loaded}")
    assert test_state == loaded
    print("Test passed!")