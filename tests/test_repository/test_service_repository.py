import unittest
from unittest.mock import MagicMock
from datetime import datetime
from botocore.exceptions import ClientError
from fastapi import status

from app.repository.service_request_repository import ServiceRequestRepository
from app.app_exception.app_exception import AppException
from app.models.service_request import ServiceRequest, ServiceStatus, ServiceType


class TestServiceRequestRepository(unittest.TestCase):
    def setUp(self):
        self.mock_ddb_resource = MagicMock()
        self.mock_table = MagicMock()
        self.mock_ddb_client = MagicMock()

        self.mock_ddb_resource.Table.return_value = self.mock_table
        self.mock_ddb_resource.meta.client = self.mock_ddb_client

        self.repo = ServiceRequestRepository(
            ddb_resource=self.mock_ddb_resource,
            table_name="test-table",
        )

        self.service_request = ServiceRequest(
            id="sr-1",
            user_id="user-1",
            booking_id="booking-1",
            room_num=101,
            type=ServiceType.CLEANING,
            status=ServiceStatus.PENDING,
            is_assigned=False,
            assigned_to=None,
            details="Clean room",
            created_at=datetime.now(),
        )

    def test_save_service_request_success(self):
        self.repo.save_service_request(self.service_request)

        self.mock_ddb_client.transact_write_items.assert_called_once()

    def test_save_service_request_conflict(self):
        error_response = {
            "Error": {"Code": "TransactionCanceledException"},
            "CancellationReasons": [{"Code": "ConditionalCheckFailed"}],
        }

        self.mock_ddb_client.transact_write_items.side_effect = ClientError(
            error_response=error_response,
            operation_name="TransactWriteItems",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.save_service_request(self.service_request)

        self.assertEqual(ctx.exception.status_code, status.HTTP_409_CONFLICT)

    def test_save_service_request_ddb_error(self):
        self.mock_ddb_client.transact_write_items.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="TransactWriteItems",
        )

        with self.assertRaises(AppException):
            self.repo.save_service_request(self.service_request)

    def test_get_all_pending_service_requests_success(self):
        self.mock_table.query.return_value = {
            "Items": [self.service_request.model_dump(mode="json")]
        }

        result = self.repo.get_all_pending_service_requests()

        self.assertEqual(len(result), 1)

    def test_get_all_pending_service_requests_ddb_error(self):
        self.mock_table.query.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="Query",
        )

        with self.assertRaises(AppException):
            self.repo.get_all_pending_service_requests()

    def test_get_pending_service_requests_by_user_success(self):
        self.mock_table.query.return_value = {
            "Items": [self.service_request.model_dump(mode="json")]
        }

        result = self.repo.get_pending_service_requests_by_user_id("user-1")

        self.assertEqual(len(result), 1)

    def test_get_pending_service_requests_by_user_ddb_error(self):
        self.mock_table.query.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="Query",
        )

        with self.assertRaises(AppException):
            self.repo.get_pending_service_requests_by_user_id("user-1")

    def test_assign_service_request_success(self):
        self.mock_table.get_item.return_value = {
            "Item": self.service_request.model_dump(mode="json")
        }

        self.repo.assign_service_request("sr-1", "emp-1")

        self.mock_ddb_client.transact_write_items.assert_called_once()

    def test_assign_service_request_not_found(self):
        self.mock_table.get_item.return_value = {}

        with self.assertRaises(AppException) as ctx:
            self.repo.assign_service_request("sr-1", "emp-1")

        self.assertEqual(ctx.exception.status_code, status.HTTP_404_NOT_FOUND)

    def test_assign_service_request_already_assigned(self):
        self.mock_table.get_item.return_value = {
            "Item": self.service_request.model_dump(mode="json")
        }

        self.mock_ddb_client.transact_write_items.side_effect = ClientError(
            error_response={"Error": {"Code": "TransactionCanceledException"}},
            operation_name="TransactWriteItems",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.assign_service_request("sr-1", "emp-1")

        self.assertEqual(ctx.exception.status_code, status.HTTP_409_CONFLICT)

    def test_get_assigned_service_requests_success(self):
        self.mock_table.query.return_value = {
            "Items": [self.service_request.model_dump(mode="json")]
        }

        result = self.repo.get_assigned_service_requests("emp-1")

        self.assertEqual(len(result), 1)

    def test_get_assigned_service_requests_ddb_error(self):
        self.mock_table.query.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="Query",
        )

        with self.assertRaises(AppException):
            self.repo.get_assigned_service_requests("emp-1")

    def test_get_service_request_by_id_success(self):
        self.mock_table.get_item.return_value = {
            "Item": self.service_request.model_dump(mode="json")
        }

        result = self.repo.get_service_request_by_id("sr-1")

        self.assertEqual(result.id, "sr-1")

    def test_get_service_request_by_id_not_found(self):
        self.mock_table.get_item.return_value = {}

        with self.assertRaises(AppException):
            self.repo.get_service_request_by_id("sr-1")

    def test_get_service_request_by_id_ddb_error(self):
        self.mock_table.get_item.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="GetItem",
        )

        with self.assertRaises(AppException):
            self.repo.get_service_request_by_id("sr-1")

    def test_update_service_request_success(self):
        assigned_item = self.service_request.model_dump(mode="json")
        assigned_item["assigned_to"] = "emp-1"

        self.mock_table.get_item.return_value = {"Item": assigned_item}

        self.repo.update_service_request("sr-1", ServiceStatus.DONE)

        self.mock_ddb_client.transact_write_items.assert_called_once()

    def test_update_service_request_not_found(self):
        self.mock_table.get_item.return_value = {}

        with self.assertRaises(AppException) as ctx:
            self.repo.update_service_request("sr-1", ServiceStatus.DONE)

        self.assertEqual(ctx.exception.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_service_request_ddb_error(self):
        self.mock_table.get_item.return_value = {
            "Item": self.service_request.model_dump(mode="json")
        }

        self.mock_ddb_client.transact_write_items.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="TransactWriteItems",
        )

        with self.assertRaises(AppException):
            self.repo.update_service_request("sr-1", ServiceStatus.DONE)
