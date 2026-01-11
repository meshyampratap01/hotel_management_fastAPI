import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.feedback_service import FeedbackService
from app.dtos.feedback_dtos import CreateFeedbackDTO
from app.models.feedbacks import Feedback


class TestFeedbackService(unittest.TestCase):
    def setUp(self):
        self.mock_feedback_repo = MagicMock()
        self.service = FeedbackService(feedback_repo=self.mock_feedback_repo)

        self.current_user = {
            "sub": "user-123",
            "user_name": "Shyam",
        }

    @patch("app.services.feedback_service.uuid.uuid4")
    @patch("app.services.feedback_service.datetime")
    def test_save_feedback_success(self, mock_datetime, mock_uuid):
        fixed_time = datetime(2026, 1, 10, 10, 0, 0)
        mock_datetime.now.return_value = fixed_time
        mock_uuid.return_value = "feedback-uuid"

        request = CreateFeedbackDTO(
            rating=5,
            message="Great stay!",
        )

        self.service.save_feedback(request, self.current_user)

        self.mock_feedback_repo.save_feedback.assert_called_once()
        saved_feedback = self.mock_feedback_repo.save_feedback.call_args[0][0]

        self.assertIsInstance(saved_feedback, Feedback)
        self.assertEqual(saved_feedback.id, "feedback-uuid")
        self.assertEqual(saved_feedback.user_id, "user-123")
        self.assertEqual(saved_feedback.user_name, "Shyam")
        self.assertEqual(saved_feedback.rating, 5)
        self.assertEqual(saved_feedback.message, "Great stay!")
        self.assertEqual(saved_feedback.created_at, fixed_time)

    def test_get_all_feedbacks(self):
        feedbacks = [MagicMock(), MagicMock()]
        self.mock_feedback_repo.get_all_feedbacks.return_value = feedbacks

        result = self.service.get_all_feedbacks()

        self.assertEqual(result, feedbacks)
        self.mock_feedback_repo.get_all_feedbacks.assert_called_once()

    def test_delete_feedback(self):
        self.service.delete_feedback("feedback-123")

        self.mock_feedback_repo.delete_feedback.assert_called_once_with("feedback-123")

    def test_get_feedback_by_id_filters_by_user(self):
        fb1 = MagicMock()
        fb1.user_id = "user-123"

        fb2 = MagicMock()
        fb2.user_id = "user-999"

        fb3 = MagicMock()
        fb3.user_id = "user-123"

        self.mock_feedback_repo.get_all_feedbacks.return_value = [fb1, fb2, fb3]

        result = self.service.get_feedback_by_id(self.current_user)

        self.assertEqual(result, [fb1, fb3])
        self.mock_feedback_repo.get_all_feedbacks.assert_called_once()

    def test_get_feedback_by_id_no_feedback(self):
        fb = MagicMock()
        fb.user_id = "other-user"

        self.mock_feedback_repo.get_all_feedbacks.return_value = [fb]

        result = self.service.get_feedback_by_id(self.current_user)

        self.assertEqual(result, [])
