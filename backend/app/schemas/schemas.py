from pydantic import BaseModel
from typing import Dict, Any, Optional

class ChatRequest(BaseModel):
    question: str
    # 요청 시 사용자 프로필을 동적으로 전달할 수 있도록 만듭니다.
    user_profile: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    session_id: str
    answer: str 