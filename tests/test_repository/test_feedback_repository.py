import unittest
from unittest.mock import MagicMock
from datetime import datetime
from botocore.exceptions import ClientError
from fastapi import status

from app.repository.feedback_repository import FeedbackRepository
from app.app_exception.app_exception import AppException
from app.models.feedbacks import Feedback


class TestFeedbackRepository(unittest.TestCase):
    def setUp(self):
        self.mock_ddb_resource = MagicMock()
        self.mock_table = MagicMock()

        self.mock_ddb_resource.Table.return_value = self.mock_table

        self.repo = FeedbackRepository(
            ddb_resource=self.mock_ddb_resource,
            table_name="test-table",
        )

        self.feedback = Feedback(
            id="fb-1",
            user_id="user-1",
            user_name="John",
            message="Great stay!",
            rating=5,
            created_at=datetime.now(),
        )

    def test_save_feedback_success(self):
        self.repo.save_feedback(self.feedback)

        self.mock_table.put_item.assert_called_once()

    def test_save_feedback_ddb_error(self):
        self.mock_table.put_item.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="PutItem",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.save_feedback(self.feedback)

        self.assertEqual(
            ctx.exception.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def test_get_all_feedbacks_success(self):
        self.mock_table.query.return_value = {
            "Items": [
                self.feedback.model_dump(mode="json"),
            ]
        }

        result = self.repo.get_all_feedbacks()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "fb-1")

    def test_get_all_feedbacks_empty(self):
        self.mock_table.query.return_value = {"Items": []}

        result = self.repo.get_all_feedbacks()

        self.assertEqual(result, [])

    def test_get_all_feedbacks_ddb_error(self):
        self.mock_table.query.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="Query",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.get_all_feedbacks()

        self.assertEqual(
            ctx.exception.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def test_delete_feedback_success(self):
        self.repo.delete_feedback("fb-1")

        self.mock_table.delete_item.assert_called_once()

    def test_delete_feedback_ddb_error(self):
        self.mock_table.delete_item.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="DeleteItem",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.delete_feedback("fb-1")

        self.assertEqual(
            ctx.exception.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
