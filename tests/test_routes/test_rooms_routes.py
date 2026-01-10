import unittest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.app import app
from app.services.room_service import RoomService
from app.dependencies import get_ddb_resource, get_table_name


class TestRoomRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.mock_room_service = Mock(spec=RoomService)

        self.mock_guest_user = {
            "sub": "guest-1",
            "userName": "guest",
            "role": "Guest",
        }

        self.mock_manager_user = {
            "sub": "manager-1",
            "userName": "manager",
            "role": "Manager",
        }

        app.dependency_overrides[RoomService] = lambda: self.mock_room_service
        app.dependency_overrides[get_ddb_resource] = lambda: Mock()
        app.dependency_overrides[get_table_name] = lambda: "RoomsTable"

    def tearDown(self):
        app.dependency_overrides.clear()

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_get_rooms_as_manager_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_manager_user

        rooms = [
            {"number": 101, "type": "Deluxe"},
            {"number": 102, "type": "Standard"},
        ]

        self.mock_room_service.get_all_rooms.return_value = rooms

        response = self.client.get("/rooms/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Rooms Fetched Successfully")
        self.assertEqual(response.json()["data"], rooms)

        self.mock_room_service.get_all_rooms.assert_called_once()

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_get_rooms_as_guest_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_guest_user

        rooms = [
            {"number": 201, "type": "Standard"},
        ]

        self.mock_room_service.get_available_rooms.return_value = rooms

        response = self.client.get("/rooms/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Rooms Fetched Successfully")
        self.assertEqual(response.json()["data"], rooms)

        self.mock_room_service.get_available_rooms.assert_called_once()

    def test_get_rooms_unauthorized(self):
        response = self.client.get("/rooms/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_get_rooms_forbidden_for_wrong_role(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = {
            "sub": "emp-1",
            "role": "CleaningStaff",
        }

        response = self.client.get("/rooms/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_add_room_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_manager_user

        room_response = {"number": 301, "type": "Deluxe"}

        self.mock_room_service.add_room.return_value = room_response

        payload = {
            "number": 301,
            "type": "Deluxe",
            "price": 3000,
            "description": "Sea view",
        }

        response = self.client.post("/rooms/", json=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["message"], "Room added successfully")
        self.assertEqual(response.json()["data"], room_response)

        self.mock_room_service.add_room.assert_called_once()

    def test_add_room_unauthorized(self):
        response = self.client.post("/rooms/", json={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_add_room_forbidden_for_guest(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_guest_user

        response = self.client.post("/rooms/", json={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_delete_room_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_manager_user

        response = self.client.delete("/rooms/101")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Room deleted successfully")

        self.mock_room_service.delete_room.assert_called_once_with(101)

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_delete_room_forbidden_for_guest(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_guest_user

        response = self.client.delete("/rooms/101")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_update_room_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_manager_user

        payload = {
            "price": 3500,
            "description": "Updated description",
        }

        response = self.client.patch("/rooms/101", json=payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Room updated successfully")

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_update_room_forbidden_for_guest(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_guest_user

        response = self.client.patch("/rooms/101", json={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
