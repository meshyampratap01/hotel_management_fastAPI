import unittest
from unittest.mock import MagicMock
from botocore.exceptions import ClientError
from fastapi import status

from app.repository.user_repository import UserRepository
from app.app_exception.app_exception import AppException
from app.models.users import User, Role


class TestUserRepository(unittest.TestCase):
    def setUp(self):
        self.mock_ddb_resource = MagicMock()
        self.mock_table = MagicMock()
        self.mock_ddb_client = MagicMock()

        self.mock_ddb_resource.Table.return_value = self.mock_table
        self.mock_ddb_resource.meta.client = self.mock_ddb_client

        self.repo = UserRepository(
            ddb_resource=self.mock_ddb_resource,
            table_name="test-table",
        )

        self.user = User(
            id="user-1",
            name="John Doe",
            email="john@example.com",
            password="hashed-password",
            role=Role.GUEST,
            available=False,
        )

    def test_save_user_success(self):
        self.repo.save_user(self.user)

        self.mock_ddb_client.transact_write_items.assert_called_once()

    def test_save_user_email_conflict(self):
        error_response = {
            "Error": {"Code": "TransactionCanceledException"},
            "CancellationReasons": [{"Code": "ConditionalCheckFailed"}],
        }

        self.mock_ddb_client.transact_write_items.side_effect = ClientError(
            error_response=error_response,
            operation_name="TransactWriteItems",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.save_user(self.user)

        self.assertEqual(ctx.exception.status_code, status.HTTP_409_CONFLICT)

    def test_save_user_ddb_error(self):
        self.mock_ddb_client.transact_write_items.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="TransactWriteItems",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.save_user(self.user)

        self.assertEqual(
            ctx.exception.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def test_get_user_by_email_success(self):
        self.mock_table.query.return_value = {"Items": [{"user_id": "user-1"}]}

        self.mock_table.get_item.return_value = {"Item": self.user.model_dump()}

        result = self.repo.get_user_by_email("john@example.com")

        self.assertEqual(result.id, "user-1")
        self.assertEqual(result.email, "john@example.com")

    def test_get_user_by_email_not_found(self):
        self.mock_table.query.return_val
