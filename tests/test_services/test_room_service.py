import unittest
from unittest.mock import MagicMock, patch

from fastapi import status

from app.models import rooms
from app.services.room_service import RoomService
from app.app_exception.app_exception import AppException
from app.dtos.room_requests import AddRoomRequest, UpdateRoomRequest


class TestRoomService(unittest.TestCase):
    def setUp(self):
        self.mock_room_repo = MagicMock()
        self.service = RoomService(room_repo=self.mock_room_repo)

    def test_get_all_rooms(self):
        rooms = [MagicMock(), MagicMock()]
        self.mock_room_repo.get_all_rooms.return_value = rooms

        result = self.service.get_all_rooms()

        self.assertEqual(result, rooms)
        self.mock_room_repo.get_all_rooms.assert_called_once()

    def test_get_available_rooms(self):
        rooms = [MagicMock()]
        self.mock_room_repo.get_available_rooms.return_value = rooms

        result = self.service.get_available_rooms()

        self.assertEqual(result, rooms)
        self.mock_room_repo.get_available_rooms.assert_called_once()

    @patch("app.services.room_service.uuid.uuid4")
    def test_add_room_success(self, mock_uuid):
        mock_uuid.return_value = "room-uuid"

        request = AddRoomRequest(
            number=101,
            type=rooms.RoomType.RoomTypeStandard,
            price=2000,
            description="Nice room",
        )

        room = self.service.add_room(request)

        self.assertEqual(room.id, "room-uuid")
        self.assertEqual(room.number, 101)
        self.assertEqual(room.price, 2000)
        self.assertTrue(room.is_available)

        self.mock_room_repo.add_room.assert_called_once_with(room)

    def test_delete_room_success(self):
        room = MagicMock()
        room.is_available = True

        self.mock_room_repo.get_room_by_number.return_value = room

        self.service.delete_room(101)

        self.mock_room_repo.delete_room.assert_called_once_with(101)

    def test_delete_room_room_not_available(self):
        room = MagicMock()
        room.is_available = False

        self.mock_room_repo.get_room_by_number.return_value = room

        with self.assertRaises(AppException) as ctx:
            self.service.delete_room(101)

        self.assertEqual(ctx.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ctx.exception.message, "Room is booked and cannot be deleted")

        self.mock_room_repo.delete_room.assert_not_called()

    def test_update_room_no_fields_provided(self):
        request = UpdateRoomRequest()

        with self.assertRaises(AppException) as ctx:
            self.service.update_room(101, request)

        self.assertEqual(ctx.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ctx.exception.message, "No fields provided for update")

        self.mock_room_repo.update_room.assert_not_called()

    def test_update_room_success(self):
        request = UpdateRoomRequest(
            price=2500,
            is_available=False,
        )

        self.service.update_room(101, request)

        self.mock_room_repo.update_room.assert_called_once_with(
            101,
            {
                "price": 2500,
                "is_available": False,
            },
        )

    def test_update_room_update_fields_empty_after_processing(self):
        request = UpdateRoomRequest(
            type=None,
            price=None,
            is_available=None,
            description=None,
        )

        with self.assertRaises(AppException):
            self.service.update_room(101, request)
