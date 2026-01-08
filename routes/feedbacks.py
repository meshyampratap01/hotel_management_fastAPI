from fastapi import APIRouter, Depends, status

from dependencies import get_feedback_service, require_roles
from dtos.feedback_dtos import CreateFeedbackDTO
from models.roles import Role
from services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedbacks")


@router.post("/", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    feedback_dto: CreateFeedbackDTO,
    current_user=Depends(require_roles((Role.GUEST.value))),
    feedback_service: FeedbackService = Depends(get_feedback_service),
):
    feedback_service.save_feedback(feedback_dto, current_user)
    return {"detail": "feedback successfully submitted"}


@router.get("/", status_code=status.HTTP_200_OK)
def get_feedback_by_role(
    current_user=Depends(require_roles(Role.GUEST.value, Role.MANAGER.value)),
    feedback_service: FeedbackService = Depends(get_feedback_service),
):
    role = current_user.get("role")
    if role == Role.MANAGER.value:
        return feedback_service.get_all_feedbacks()
    elif role == Role.GUEST.value:
        return feedback_service.get_feedback_by_id(current_user)


@router.delete("/{feedback_id}", status_code=status.HTTP_200_OK)
def delete_feedback(
    feedback_id: str,
    _=Depends(require_roles(Role.MANAGER.value)),
    feedback_service: FeedbackService = Depends(get_feedback_service),
):
    feedback_service.delete_feedback(feedback_id)
    return {"detail": "feedback successfully deleted"}
