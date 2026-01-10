from typing import List
import uuid
from datetime import datetime

from fastapi import Depends
from app.dtos.feedback_dtos import CreateFeedbackDTO
from app.models.feedbacks import Feedback
from app.repository.feedback_repository import FeedbackRepository


class FeedbackService:
    def __init__(self, feedback_repo: FeedbackRepository = Depends(FeedbackRepository)):
        self.feedback_repo = feedback_repo

    def save_feedback(self, request: CreateFeedbackDTO, current_user) -> None:
        new_feedback = Feedback(
            id=str(uuid.uuid4()),
            user_id=current_user.get("sub"),
            rating=request.rating,
            user_name=current_user.get("user_name"),
            message=request.message,
            created_at=datetime.now(),
        )
        self.feedback_repo.save_feedback(new_feedback)

    def get_all_feedbacks(self) -> List[Feedback]:
        feedbacks = self.feedback_repo.get_all_feedbacks()
        return feedbacks

    def delete_feedback(self, feedback_id: str) -> None:
        self.feedback_repo.delete_feedback(feedback_id)

    def get_feedback_by_id(self, current_user) -> List[Feedback]:
        user_id = current_user.get("sub")
        feedbacks = self.feedback_repo.get_all_feedbacks()
        return [feedback for feedback in feedbacks if feedback.user_id == user_id]
