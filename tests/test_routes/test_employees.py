import unittest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.app import app
from app.services.employee_service import EmployeeService
from app.services.service_request_service import ServiceRequestService
from app.dependencies import get_ddb_resource, get_table_name


class TestEmployeeRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.mock_employee_service = Mock(spec=EmployeeService)
        self.mock_service_request_service = Mock(spec=ServiceRequestService)

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

        app.dependency_overrides[EmployeeService] = lambda: self.mock_employee_service
        app.dependency_overrides[ServiceRequestService] = (
            lambda: self.mock_service_request_service
        )
        app.dependency_overrides[get_ddb_resource] = lambda: Mock()
        app.dependency_overrides[get_table_name] = lambda: "EmployeesTable"

    def tearDown(self):
        app.dependency_overrides.clear()

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_create_employee_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_manager_user

        payload = {
            "name": "John Doe",
            "password": "122345678",
            "email": "john@example.com",
            "role": "CleaningStaff",
            "available": True,
        }

        response = self.client.post("/employees/", json=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["message"], "Employee created successfully")

        self.mock_employee_service.create_employee.assert_called_once()

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_get_employees_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_manager_user

        employees_response = [
            {"id": "emp-1", "name": "John"},
            {"id": "emp-2", "name": "Jane"},
        ]

        self.mock_employee_service.get_employees.return_value = employees_response

        response = self.client.get("/employees/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Employees Fetched Successfully")
        self.assertEqual(response.json()["data"], employees_response)

        self.mock_employee_service.get_employees.assert_called_once()

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_update_employee_availability_success(
        self, mock_verify_jwt, mock_get_token
    ):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_staff_user

        payload = {
            "available": True,
        }

        employee_id = "emp-123"

        response = self.client.patch(
            f"/employees/availability/{employee_id}", json=payload
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["message"],
            "Employee availability updated successfully",
        )

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_delete_employee_success(self, mock_verify_jwt, mock_get_token):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_manager_user

        employee_id = "emp-456"

        response = self.client.delete(f"/employees/{employee_id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Employee deleted successfully")

        self.mock_employee_service.delete_employee.assert_called_once_with(employee_id)

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_get_assigned_service_requests_success(
        self, mock_verify_jwt, mock_get_token
    ):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_staff_user

        service_requests_response = [
            {"id": "sr-1", "status": "Pending"},
            {"id": "sr-2", "status": "Assigned"},
        ]

        self.mock_service_request_service.get_assigned_service_requests.return_value = (
            service_requests_response
        )

        response = self.client.get("/employees/service-requests")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["message"],
            "Service requests fetched successfully",
        )
        self.assertEqual(response.json()["data"], service_requests_response)

        self.mock_service_request_service.get_assigned_service_requests.assert_called_once_with(
            self.mock_staff_user
        )

    @patch("app.dependencies.get_token")
    @patch("app.utils.jwt.verify_jwt")
    def test_update_service_request_status_success(
        self, mock_verify_jwt, mock_get_token
    ):
        mock_get_token.return_value = "token"
        mock_verify_jwt.return_value = self.mock_staff_user

        payload = {
            "status": "Done",
        }

        service_request_id = "sr-789"

        response = self.client.put(
            f"/employees/service-requests/status/{service_request_id}",
            json=payload,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["message"],
            "Service request status updated successfully",
        )
