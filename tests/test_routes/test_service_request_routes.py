import unittest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.app import app
from app.services.service_request_service import ServiceRequestService
from app.dependencies import get_ddb_resource, get_table_name


class TestServiceRequestRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.mock_service_request_service = Mock(spec=ServiceRequestService)

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

        app.dependency_overrides[ServiceRequestService] = (
            lambda: self.mock_service_request_service
        )
        app.dependency_overrides[get_ddb_resource] = lambda: Mock()
        app.dependency_overrides[get_table_name] = lambda: "ServiceRequestsTable"

    def tearDown(self):
        app.dependency_overrides.clear()

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_create_service_request_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_guest_user

        payload = {
            "room_num": 101,
            "type": "Cleaning",
            "details": "Room needs cleaning",
        }

        response = self.client.post("/service-requests/", json=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.json()["message"],
            "Service request created successfully",
        )

    def test_create_service_request_unauthorized(self):
        response = self.client.post("/service-requests/", json={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_create_service_request_forbidden_for_manager(
        self, mock_verify_jwt, mock_get_token
    ):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_manager_user

        response = self.client.post("/service-requests/", json={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_get_service_requests_as_manager_success(
        self, mock_verify_jwt, mock_get_token
    ):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_manager_user

        requests_response = [
            {"id": "sr-1", "status": "Pending"},
            {"id": "sr-2", "status": "Pending"},
        ]

        self.mock_service_request_service.get_all_pending_service_requests.return_value = requests_response

        response = self.client.get("/service-requests/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["message"],
            "Service requests fetched successfully",
        )
        self.assertEqual(response.json()["data"], requests_response)

        self.mock_service_request_service.get_all_pending_service_requests.assert_called_once()

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_get_service_requests_as_guest_success(
        self, mock_verify_jwt, mock_get_token
    ):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_guest_user

        requests_response = [
            {"id": "sr-3", "status": "Pending"},
        ]

        self.mock_service_request_service.get_service_request_by_userID.return_value = (
            requests_response
        )

        response = self.client.get("/service-requests/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["message"],
            "Service requests fetched successfully",
        )
        self.assertEqual(response.json()["data"], requests_response)

        self.mock_service_request_service.get_service_request_by_userID.assert_called_once_with(
            self.mock_guest_user
        )

    def test_get_service_requests_unauthorized(self):
        response = self.client.get("/service-requests/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_get_service_requests_forbidden_for_wrong_role(
        self, mock_verify_jwt, mock_get_token
    ):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = {
            "sub": "emp-1",
            "role": "CleaningStaff",
        }

        response = self.client.get("/service-requests/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_assign_service_request_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_manager_user

        payload = {
            "employee_id": "emp-123",
        }

        service_request_id = "sr-123"

        response = self.client.post(
            f"/service-requests/assign/{service_request_id}",
            json=payload,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["message"],
            "Service request assigned successfully",
        )

    def test_assign_service_request_unauthorized(self):
        response = self.client.post("/service-requests/assign/sr-1", json={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_assign_service_request_forbidden_for_guest(
        self, mock_verify_jwt, mock_get_token
    ):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_guest_user

        response = self.client.post("/service-requests/assign/sr-1", json={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
