import unittest
from unittest.mock import MagicMock
from botocore.exceptions import ClientError
from fastapi import status

from app.repository.employee_repository import EmployeeRepository
from app.app_exception.app_exception import AppException
from app.models.users import User, Role


class TestEmployeeRepository(unittest.TestCase):
    def setUp(self):
        self.mock_ddb_resource = MagicMock()
        self.mock_table = MagicMock()
        self.mock_ddb_client = MagicMock()

        self.mock_ddb_resource.Table.return_value = self.mock_table
        self.mock_ddb_resource.meta.client = self.mock_ddb_client

        self.repo = EmployeeRepository(
            ddb_resource=self.mock_ddb_resource,
            table_name="test-table",
        )

        self.user = User(
            id="emp-1",
            name="John Doe",
            email="john@example.com",
            password="hashed",
            role=Role.CLEANING_STAFF,
            available=True,
        )

    def test_create_employee_success(self):
        self.repo.create_employee(self.user)

        self.mock_ddb_client.transact_write_items.assert_called_once()

    def test_create_employee_email_conflict(self):
        error_response = {
            "Error": {"Code": "TransactionCanceledException"},
            "CancellationReasons": [{"Code": "ConditionalCheckFailed"}],
        }

        self.mock_ddb_client.transact_write_items.side_effect = ClientError(
            error_response=error_response,
            operation_name="TransactWriteItems",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.create_employee(self.user)

        self.assertEqual(ctx.exception.status_code, status.HTTP_409_CONFLICT)

    def test_create_employee_ddb_error(self):
        self.mock_ddb_client.transact_write_items.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="TransactWriteItems",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.create_employee(self.user)

        self.assertEqual(
            ctx.exception.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def test_get_employees_success(self):
        self.mock_table.query.return_value = {
            "Items": [
                {
                    "id": "emp-1",
                    "name": "John",
                    "email": "john@example.com",
                    "role": Role.CLEANING_STAFF,
                    "available": True,
                }
            ]
        }

        result = self.repo.get_employees()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "emp-1")

    def test_get_employees_ddb_error(self):
        self.mock_table.query.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="Query",
        )

        with self.assertRaises(AppException):
            self.repo.get_employees()

    def test_update_employee_availability_success(self):
        self.repo.update_employee_availability("emp-1", False)

        self.mock_table.update_item.assert_called_once()

    def test_update_employee_availability_not_found(self):
        self.mock_table.update_item.side_effect = ClientError(
            error_response={"Error": {"Code": "ConditionalCheckFailedException"}},
            operation_name="UpdateItem",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.update_employee_availability("emp-1", False)

        self.assertEqual(ctx.exception.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_employee_availability_ddb_error(self):
        self.mock_table.update_item.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="UpdateItem",
        )

        with self.assertRaises(AppException):
            self.repo.update_employee_availability("emp-1", False)

    def test_get_employee_by_id_success(self):
        self.mock_table.get_item.return_value = {
            "Item": {
                "id": "emp-1",
                "name": "John",
                "email": "john@example.com",
                "role": Role.CLEANING_STAFF,
                "available": True,
            }
        }

        result = self.repo.get_employee_by_id("emp-1")

        self.assertEqual(result.id, "emp-1")

    def test_get_employee_by_id_not_found(self):
        self.mock_table.get_item.return_value = {}

        with self.assertRaises(AppException) as ctx:
            self.repo.get_employee_by_id("emp-1")

        self.assertEqual(ctx.exception.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_employee_by_id_ddb_error(self):
        self.mock_table.get_item.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="GetItem",
        )

        with self.assertRaises(AppException):
            self.repo.get_employee_by_id("emp-1")

    def test_delete_employee_success(self):
        self.repo.delete_employee("emp-1", "john@example.com")

        self.mock_ddb_client.transact_write_items.assert_called_once()

    def test_delete_employee_ddb_error(self):
        self.mock_ddb_client.transact_write_items.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="TransactWriteItems",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.delete_employee("emp-1", "john@example.com")

        self.assertEqual(
            ctx.exception.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
