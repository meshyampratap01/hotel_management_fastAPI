import unittest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.app import app
from app.app_exception.app_exception import AppException
from app.services.user_service import UserService
from app.dependencies import get_ddb_resource, get_table_name


class TestProfileRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.mock_user_service = Mock(spec=UserService)

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

        self.mock_staff_user = {
            "sub": "staff-1",
            "userName": "staff",
            "role": "CleaningStaff",
        }

        app.dependency_overrides[UserService] = lambda: self.mock_user_service
        app.dependency_overrides[get_ddb_resource] = lambda: Mock()
        app.dependency_overrides[get_table_name] = lambda: "UsersTable"

    def tearDown(self):
        app.dependency_overrides.clear()

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_get_profile_as_guest_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_guest_user

        profile_response = {
            "id": "guest-1",
            "name": "Guest User",
            "email": "guest@example.com",
            "role": "Guest",
            "available": True,
        }

        self.mock_user_service.get_profile.return_value = profile_response

        response = self.client.get("/profile/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Profile Fetched Successfully")
        self.assertEqual(response.json()["data"], profile_response)

        self.mock_user_service.get_profile.assert_called_once_with("guest-1")

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_get_profile_as_manager_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_manager_user

        profile_response = {
            "id": "manager-1",
            "name": "Manager User",
            "email": "manager@example.com",
            "role": "Manager",
            "available": True,
        }

        self.mock_user_service.get_profile.return_value = profile_response

        response = self.client.get("/profile/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Profile Fetched Successfully")
        self.assertEqual(response.json()["data"], profile_response)

        self.mock_user_service.get_profile.assert_called_once_with("manager-1")

    def test_get_profile_unauthorized(self):
        response = self.client.get("/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_get_profile_forbidden_for_wrong_role(
        self, mock_verify_jwt, mock_get_token
    ):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = {
            "sub": "random-1",
            "role": "RandomRole",
        }

        response = self.client.get("/profile/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_get_profile_service_failure(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_guest_user

        self.mock_user_service.get_profile.side_effect = AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal Server Error",
        )

        response = self.client.get("/profile/")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
