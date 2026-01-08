from typing import List
import uuid
from datetime import datetime
from dtos.feedback_dtos import CreateFeedbackDTO
from models.feedbacks import Feedback
from repository.feedback_repository import DDBFeedbackRepository


class FeedbackService:
    def __init__(self, feedback_repo: DDBFeedbackRepository):
        self.feedback_repo = feedback_repo

    def save_feedback(self, request: CreateFeedbackDTO, current_user):
        new_feedback = Feedback(
            id=str(uuid.uuid4()),
            user_id=current_user.get("sub"),
            rating=request.rating,
            user_name=current_user.get("user_name"),
            message=request.message,
            created_at=datetime.now(),
        )
        try:
            self.feedback_repo.save_feedback(new_feedback)
        except Exception:
            raise

    def get_all_feedbacks(self):
        try:
            return self.feedback_repo.get_all_feedbacks()
        except Exception:
            raise

    def delete_feedback(self, feedback_id: str):
        try:
            self.feedback_repo.delete_feedback(feedback_id)
        except Exception:
            raise

    def get_feedback_by_id(self, current_user) -> List[Feedback]:
        user_id = current_user.get("sub")
        feedbacks = self.feedback_repo.get_all_feedbacks()
        return [feedback for feedback in feedbacks if feedback.user_id == user_id]
