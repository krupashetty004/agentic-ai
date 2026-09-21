from fastapi import APIRouter, Depends

from app.config.settings import settings
from app.dependencies.auth_dependencies import get_current_user
from app.models.auth_models import UserResponse
from app.models.feedback_models import FeedbackMetrics, FeedbackRequest, FeedbackResponse
from app.services.feedback_service import FeedbackService


router = APIRouter(prefix=settings.api_prefix, tags=["feedback"])
feedback_service = FeedbackService()


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(
    request: FeedbackRequest,
    current_user: UserResponse = Depends(get_current_user),
) -> FeedbackResponse:
    feedback_id = feedback_service.save(
        {
            "user": current_user.email,
            **request.model_dump(),
        }
    )
    review_required = request.rating == "down" and not request.approved
    return FeedbackResponse(
        status="recorded",
        feedback_id=feedback_id,
        review_required=review_required,
    )


@router.get("/feedback/metrics", response_model=FeedbackMetrics)
def get_feedback_metrics(
    current_user: UserResponse = Depends(get_current_user),
) -> FeedbackMetrics:
    return FeedbackMetrics(**feedback_service.metrics())
