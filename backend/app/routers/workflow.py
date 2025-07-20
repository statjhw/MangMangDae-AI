from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from app.schemas.workflow_schema import UserInfo, WorkflowResponse
from app.services.analysis_service import analysis_service
import logging
from pydantic import ValidationError

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/workflow", response_model=WorkflowResponse)
async def run_workflow(user_info: UserInfo):
    """
    사용자 정보를 받아 AI 기반 커리어 분석을 실행하고 결과를 반환합니다.
    
    Args:
        user_info: 사용자 정보 (UserInfo 모델)
        
    Returns:
        WorkflowResponse: 분석 결과
    """
    try:
        logger.info(f"워크플로우 요청 받음: {user_info.candidate_major}, {user_info.candidate_interest}")
        logger.info(f"전체 요청 데이터: {user_info.dict()}")
        
        # 사용자 정보 검증
        if not user_info.candidate_question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="질문을 입력해주세요."
            )
        
        if not user_info.candidate_interest.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="관심분야를 입력해주세요."
            )
        
        # 분석 서비스 호출
        result = await analysis_service.analyze_user_info(user_info)
        
        logger.info("워크플로우 분석 완료")
        return result
        
    except ValidationError as e:
        logger.error(f"유효성 검사 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"데이터 유효성 검사 실패: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"워크플로우 처리 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다."
        )

@router.get("/workflow/health")
async def workflow_health_check():
    """워크플로우 서비스 상태 확인"""
    return {"status": "healthy", "service": "workflow"} 