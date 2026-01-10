import unittest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.app import app
from app.services.feedback_service import FeedbackService
from app.dependencies import get_ddb_resource, get_table_name


class TestFeedbackRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.mock_feedback_service = Mock(spec=FeedbackService)

        self.mock_guest_user = {
            "sub": "user-123",
            "userName": "guest_user",
            "role": "Guest",
        }

        self.mock_manager_user = {
            "sub": "manager-123",
            "userName": "manager_user",
            "role": "Manager",
        }

        app.dependency_overrides[FeedbackService] = lambda: self.mock_feedback_service
        app.dependency_overrides[get_ddb_resource] = lambda: Mock()
        app.dependency_overrides[get_table_name] = lambda: "FeedbacksTable"

    def tearDown(self):
        app.dependency_overrides.clear()

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_submit_feedback_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_guest_user

        payload = {
            "message": "Great stay!",
            "rating": 5,
            "booking_id": "booking-1",
            "room_num": 101,
        }

        response = self.client.post("/feedbacks/", json=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["message"], "Feedback submitted successfully")

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_get_feedbacks_as_manager_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_manager_user

        feedbacks_response = [
            {"id": "fb-1", "message": "Nice service"},
            {"id": "fb-2", "message": "Room was clean"},
        ]

        self.mock_feedback_service.get_all_feedbacks.return_value = feedbacks_response

        response = self.client.get("/feedbacks/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Feedbacks Fetched Successfully")
        self.assertEqual(response.json()["data"], feedbacks_response)

        self.mock_feedback_service.get_all_feedbacks.assert_called_once()

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_get_feedbacks_as_guest_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_guest_user

        feedbacks_response = [
            {"id": "fb-1", "message": "Loved the stay"},
        ]

        self.mock_feedback_service.get_feedback_by_id.return_value = feedbacks_response

        response = self.client.get("/feedbacks/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Feedbacks Fetched Successfully")
        self.assertEqual(response.json()["data"], feedbacks_response)

        self.mock_feedback_service.get_feedback_by_id.assert_called_once_with(
            self.mock_guest_user
        )

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_delete_feedback_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_manager_user

        feedback_id = "fb-123"

        response = self.client.delete(f"/feedbacks/{feedback_id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Feedback deleted successfully")

        self.mock_feedback_service.delete_feedback.assert_called_once_with(feedback_id)
