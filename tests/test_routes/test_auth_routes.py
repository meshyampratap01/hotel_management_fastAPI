import unittest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from starlette import status

from app.app import app
from app.app_exception.app_exception import AppException
from app.services.user_service import UserService


class TestAuthRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.mock_user_service = Mock(spec=UserService)

        app.dependency_overrides[UserService] = lambda: self.mock_user_service

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_signup_success(self):
        payload = {
            "name": "test",
            "email": "test@example.com",
            "password": "12@Password",
        }

        self.mock_user_service.signup.return_value = None

        response = self.client.post("/auth/signup", json=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["message"], "User created successfully")

        self.mock_user_service.signup.assert_called_once()

    def test_signup_validation_error(self):
        response = self.client.post("/auth/signup", json={})

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)
        self.assertIn("detail", response.json())

    def test_login_success(self):
        payload = {"email": "test@example.com", "password": "password123"}

        self.mock_user_service.login.return_value = "jwt-token"

        response = self.client.post("/auth/login", json=payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.mock_user_service.login.assert_called_once()

    def test_login_invalid_credentials(self):
        payload = {"email": "wrong@example.com", "password": "wrongpassword"}

        self.mock_user_service.login.side_effect = AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid email or password",
        )

        response = self.client.post("/auth/login", json=payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["error"], "Invalid email or password")
