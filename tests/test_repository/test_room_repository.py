import unittest
from unittest.mock import MagicMock
from botocore.exceptions import ClientError
from fastapi import status

from app.repository.room_repository import RoomRepository
from app.app_exception.app_exception import AppException
from app.models.rooms import Room, RoomType


class TestRoomRepository(unittest.TestCase):
    def setUp(self):
        self.mock_ddb_resource = MagicMock()
        self.mock_table = MagicMock()

        self.mock_ddb_resource.Table.return_value = self.mock_table

        self.repo = RoomRepository(
            ddb_resource=self.mock_ddb_resource,
            table_name="test-table",
        )

        self.room = Room(
            id="room-1",
            number=101,
            type=RoomType.RoomTypeStandard,
            price=2000,
            is_available=True,
            description="Standard room",
        )

    def test_add_room_success(self):
        self.repo.add_room(self.room)

        self.mock_table.put_item.assert_called_once()

    def test_add_room_already_exists(self):
        self.mock_table.put_item.side_effect = ClientError(
            error_response={"Error": {"Code": "ConditionalCheckFailedException"}},
            operation_name="PutItem",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.add_room(self.room)

        self.assertEqual(ctx.exception.status_code, status.HTTP_409_CONFLICT)

    def test_add_room_ddb_error(self):
        self.mock_table.put_item.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="PutItem",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.add_room(self.room)

        self.assertEqual(
            ctx.exception.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def test_get_room_by_number_success(self):
        self.mock_table.get_item.return_value = {
            "Item": self.room.model_dump(mode="json")
        }

        result = self.repo.get_room_by_number(101)

        self.assertEqual(result.number, 101)

    def test_get_room_by_number_not_found(self):
        self.mock_table.get_item.return_value = {}

        with self.assertRaises(AppException) as ctx:
            self.repo.get_room_by_number(101)

        self.assertEqual(ctx.exception.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_room_by_number_ddb_error(self):
        self.mock_table.get_item.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="GetItem",
        )

        with self.assertRaises(ClientError):
            self.repo.get_room_by_number(101)

    def test_update_room_availability_success(self):
        self.repo.update_room_availability(101, False)

        self.mock_table.update_item.assert_called_once()

    def test_update_room_availability_not_found(self):
        self.mock_table.update_item.side_effect = ClientError(
            error_response={"Error": {"Code": "ConditionalCheckFailedException"}},
            operation_name="UpdateItem",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.update_room_availability(101, False)

        self.assertEqual(ctx.exception.status_code, status.HTTP_409_CONFLICT)

    def test_update_room_availability_ddb_error(self):
        self.mock_table.update_item.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="UpdateItem",
        )

        with self.assertRaises(AppException):
            self.repo.update_room_availability(101, False)

    def test_get_all_rooms_success(self):
        self.mock_table.query.return_value = {
            "Items": [
                self.room.model_dump(mode="json"),
            ]
        }

        result = self.repo.get_all_rooms()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].number, 101)

    def test_get_all_rooms_empty(self):
        self.mock_table.query.return_value = {"Items": []}

        result = self.repo.get_all_rooms()

        self.assertEqual(result, [])

    def test_get_all_rooms_ddb_error(self):
        self.mock_table.query.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="Query",
        )

        with self.assertRaises(AppException):
            self.repo.get_all_rooms()

    def test_get_available_rooms_success(self):
        self.mock_table.query.return_value = {
            "Items": [
                self.room.model_dump(mode="json"),
            ]
        }

        result = self.repo.get_available_rooms()

        self.assertEqual(len(result), 1)
        self.assertTrue(result[0].is_available)

    def test_get_available_rooms_ddb_error(self):
        self.mock_table.query.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="Query",
        )

        with self.assertRaises(AppException):
            self.repo.get_available_rooms()

    def test_delete_room_success(self):
        self.repo.delete_room(101)

        self.mock_table.delete_item.assert_called_once()

    def test_delete_room_not_found(self):
        self.mock_table.delete_item.side_effect = ClientError(
            error_response={"Error": {"Code": "ConditionalCheckFailedException"}},
            operation_name="DeleteItem",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.delete_room(101)

        self.assertEqual(ctx.exception.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_room_ddb_error(self):
        self.mock_table.delete_item.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="DeleteItem",
        )

        with self.assertRaises(AppException):
            self.repo.delete_room(101)

    def test_update_room_success(self):
        fields = {
            "price": 2500,
            "description": "Updated room",
        }

        self.repo.update_room(101, fields)

        self.mock_table.update_item.assert_called_once()

    def test_update_room_not_found(self):
        self.mock_table.update_item.side_effect = ClientError(
            error_response={"Error": {"Code": "ConditionalCheckFailedException"}},
            operation_name="UpdateItem",
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.update_room(101, {"price": 3000})

        self.assertEqual(ctx.exception.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_room_ddb_error(self):
        self.mock_table.update_item.side_effect = ClientError(
            error_response={"Error": {"Code": "InternalError"}},
            operation_name="UpdateItem",
        )

        with self.assertRaises(AppException):
            self.repo.update_room(101, {"price": 3000})
