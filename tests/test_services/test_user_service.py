import unittest
from unittest.mock import MagicMock, patch

from fastapi import status

from app.services.user_service import UserService
from app.app_exception.app_exception import AppException
from app.dtos.auth_requests import UserCreateRequest, UserLoginRequest
from app.dtos.user_profile import UserProfileDTO
from app.models.users import Role


class TestUserService(unittest.TestCase):
    def setUp(self):
        self.mock_user_repo = MagicMock()
        self.service = UserService(user_repo=self.mock_user_repo)

    @patch("app.services.user_service.uuid.uuid4")
    @patch("app.services.user_service.auth.hash_password")
    def test_create_user_internal(self, mock_hash, mock_uuid):
        mock_uuid.return_value = "user-uuid"
        mock_hash.return_value = "hashed-password"

        user = self.service._create_user(
            name="Shyam",
            email="shyam@test.com",
            password="secret",
        )

        self.assertEqual(user.id, "user-uuid")
        self.assertEqual(user.name, "Shyam")
        self.assertEqual(user.email, "shyam@test.com")
        self.assertEqual(user.password, "hashed-password")
        self.assertEqual(user.role, Role.GUEST)
        self.assertFalse(user.available)

        mock_hash.assert_called_once_with("secret")

    @patch("app.services.user_service.auth.hash_password")
    def test_signup_success(self, mock_hash):
        mock_hash.return_value = "hashed"

        request = UserCreateRequest(
            name="Shyam",
            email="Shyam@TEST.com",
            password="12@Password",
        )

        self.service.signup(request)

        self.mock_user_repo.save_user.assert_called_once()
        saved_user = self.mock_user_repo.save_user.call_args[0][0]

        self.assertEqual(saved_user.email, "shyam@test.com")

    def test_signup_repo_exception_propagates(self):
        request = UserCreateRequest(
            name="Shyam",
            email="shyam@test.com",
            password="12@Password",
        )

        self.mock_user_repo.save_user.side_effect = AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="User exists",
        )

        with self.assertRaises(AppException):
            self.service.signup(request)

    def test_signup_unexpected_exception(self):
        request = UserCreateRequest(
            name="Shyam",
            email="shyam@test.com",
            password="12@Passwrod",
        )

        self.mock_user_repo.save_user.side_effect = Exception("DB down")

        with self.assertRaises(AppException) as ctx:
            self.service.signup(request)

        self.assertEqual(
            ctx.exception.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        self.assertEqual(ctx.exception.message, "Failed to create user")

    @patch("app.services.user_service.jwt.generate_jwt")
    @patch("app.services.user_service.auth.verify_password")
    def test_login_success(self, mock_verify, mock_jwt):
        user = MagicMock()
        user.id = "user-123"
        user.name = "Shyam"
        user.password = "hashed"
        user.role = Role.GUEST

        self.mock_user_repo.get_user_by_email.return_value = user
        mock_verify.return_value = True
        mock_jwt.return_value = "jwt-token"

        request = UserLoginRequest(
            email="SHYAM@test.com",
            password="secret",
        )

        token = self.service.login(request)

        self.assertEqual(token, "jwt-token")
        mock_jwt.assert_called_once()

    @patch("app.services.user_service.auth.verify_password")
    def test_login_invalid_password(self, mock_verify):
        user = MagicMock()
        user.password = "hashed"

        self.mock_user_repo.get_user_by_email.return_value = user
        mock_verify.return_value = False

        request = UserLoginRequest(
            email="test@test.com",
            password="wrong",
        )

        with self.assertRaises(AppException) as ctx:
            self.service.login(request)

        self.assertEqual(ctx.exception.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(ctx.exception.message, "Invalid email or password")

    def test_login_user_not_found(self):
        self.mock_user_repo.get_user_by_email.side_effect = AppException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="User not found",
        )

        request = UserLoginRequest(
            email="test@test.com",
            password="secret",
        )

        with self.assertRaises(AppException):
            self.service.login(request)

    @patch("app.services.user_service.auth.verify_password")
    @patch("app.services.user_service.jwt.generate_jwt")
    def test_login_jwt_exception(self, mock_jwt, mock_verify):
        user = MagicMock()
        user.id = "user-1"
        user.name = "Shyam"
        user.password = "hashed"
        user.role = Role.GUEST

        self.mock_user_repo.get_user_by_email.return_value = user
        mock_verify.return_value = True
        mock_jwt.side_effect = AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="JWT failed",
        )

        request = UserLoginRequest(
            email="test@test.com",
            password="secret",
        )

        with self.assertRaises(AppException):
            self.service.login(request)

    def test_get_profile(self):
        user = MagicMock()
        user.id = "user-123"
        user.name = "Shyam"
        user.email = "shyam@test.com"
        user.role = Role.GUEST
        user.available = True

        self.mock_user_repo.get_user_by_id.return_value = user

        profile = self.service.get_profile("user-123")

        self.assertIsInstance(profile, UserProfileDTO)
        self.assertEqual(profile.id, "user-123")
        self.assertEqual(profile.email, "shyam@test.com")
