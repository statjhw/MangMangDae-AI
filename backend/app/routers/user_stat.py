import sys
import os
from fastapi import APIRouter, Request
from fastapi.exceptions import HTTPException
from backend.app.services.StatUser import StatUser

router = APIRouter()

from pydantic import BaseModel
from typing import Dict, Any, Optional

class UserStatRequest(BaseModel):
    user_profile: Dict[str, Any]

@router.post("/user_stat")
async def get_user_stat(request: Request, stat_request: UserStatRequest):
    # 요청에서 직접 사용자 정보 가져오기
    user_profile = stat_request.user_profile
    
    user_info = {
        "candidate_major": user_profile.get("candidate_major", ""),
        "candidate_career": user_profile.get("candidate_career", ""),
        "candidate_interest": user_profile.get("candidate_interest", ""),
        "candidate_location": user_profile.get("candidate_location", ""),
        "candidate_tech_stack": user_profile.get("candidate_tech_stack", []),
        "candidate_salary": user_profile.get("candidate_salary", ""),
        "candidate_question": user_profile.get("candidate_question", "")
    }
    stat_user = StatUser()
    return stat_user.get_user_stat(user_info)