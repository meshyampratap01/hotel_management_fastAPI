from fastapi import APIRouter, Depends, status
from response.response import APIResponse

from dependencies import require_roles
from dtos.feedback_dtos import CreateFeedbackDTO
from models.users import Role
from services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedbacks")


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=APIResponse)
def submit_feedback(
    feedback_dto: CreateFeedbackDTO,
    current_user=Depends(require_roles((Role.GUEST.value))),
    feedback_service: FeedbackService = Depends(FeedbackService),
):
    feedback_service.save_feedback(feedback_dto, current_user)
    return APIResponse(
        status_code=status.HTTP_201_CREATED,
        message="Feedback submitted successfully",
    )


@router.get("/", status_code=status.HTTP_200_OK, response_model=APIResponse)
def get_feedback_by_role(
    current_user=Depends(require_roles(Role.GUEST.value, Role.MANAGER.value)),
    feedback_service: FeedbackService = Depends(FeedbackService),
):
    role = current_user.get("role")
    if role == Role.MANAGER.value:
        feedbacks = feedback_service.get_all_feedbacks()
        return APIResponse(
            status_code=status.HTTP_200_OK,
            message="Feedbacks Fetched Successfully",
            data=feedbacks,
        )

    elif role == Role.GUEST.value:
        feedbacks = feedback_service.get_feedback_by_id(current_user)
        return APIResponse(
            status_code=status.HTTP_200_OK,
            message="Feedbacks Fetched Successfully",
            data=feedbacks,
        )


@router.delete(
    "/{feedback_id}", status_code=status.HTTP_200_OK, response_model=APIResponse
)
def delete_feedback(
    feedback_id: str,
    _=Depends(require_roles(Role.MANAGER.value)),
    feedback_service: FeedbackService = Depends(FeedbackService),
):
    feedback_service.delete_feedback(feedback_id)
    return APIResponse(
        status_code=status.HTTP_200_OK,
        message="Feedback deleted successfully",
    )
