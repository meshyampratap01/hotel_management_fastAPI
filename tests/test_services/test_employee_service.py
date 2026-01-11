import unittest
from unittest.mock import MagicMock, patch

from fastapi import status

from app.services.employee_service import EmployeeService
from app.app_exception.app_exception import AppException
from app.models.users import Role
from app.dtos.employee_requests import CreateEmployeeRequest, UpdateEmployeeRequest
from app.dtos.employee_response import EmployeeResponseDTO


class TestEmployeeService(unittest.TestCase):
    def setUp(self):
        self.mock_employee_repo = MagicMock()

        self.service = EmployeeService(employee_repo=self.mock_employee_repo)

    @patch("app.services.employee_service.uuid.uuid4")
    @patch("app.services.employee_service.auth.hash_password")
    def test_create_employee_internal(self, mock_hash_password, mock_uuid):
        mock_uuid.return_value = "uuid-123"
        mock_hash_password.return_value = "hashed-password"

        user = self.service._create_employee(
            name="John",
            email="john@test.com",
            password="secret",
            role=Role.MANAGER,
        )

        self.assertEqual(user.id, "uuid-123")
        self.assertEqual(user.name, "John")
        self.assertEqual(user.email, "john@test.com")
        self.assertEqual(user.password, "hashed-password")
        self.assertEqual(user.role, Role.MANAGER)
        self.assertTrue(user.available)

        mock_hash_password.assert_called_once_with("secret")

    @patch("app.services.employee_service.auth.hash_password")
    def test_create_employee_success(self, mock_hash_password):
        mock_hash_password.return_value = "hashed"

        request = CreateEmployeeRequest(
            name="Alice",
            email="alice@test.com",
            password="password",
            role=Role.CLEANING_STAFF,
            available=True,
        )

        self.service.create_employee(request)

        self.mock_employee_repo.create_employee.assert_called_once()

    def test_create_employee_invalid_role(self):
        request = CreateEmployeeRequest(
            name="Bob",
            email="bob@test.com",
            password="password",
            role=Role.GUEST,
            available=True,
        )

        with self.assertRaises(AppException) as ctx:
            self.service.create_employee(request)

        self.assertEqual(ctx.exception.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ctx.exception.message, "Invalid role for employee")

        self.mock_employee_repo.create_employee.assert_not_called()

    def test_get_employees(self):
        emp1 = MagicMock()
        emp1.model_dump.return_value = {
            "id": "1",
            "name": "A",
            "email": "a@test.com",
            "role": Role.MANAGER,
            "available": True,
        }

        emp2 = MagicMock()
        emp2.model_dump.return_value = {
            "id": "2",
            "name": "B",
            "email": "b@test.com",
            "role": Role.KITCHEN_STAFF,
            "available": False,
        }

        self.mock_employee_repo.get_employees.return_value = [emp1, emp2]

        result = self.service.get_employees()

        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], EmployeeResponseDTO)
        self.assertIsInstance(result[1], EmployeeResponseDTO)

        self.mock_employee_repo.get_employees.assert_called_once()

    def test_update_employee_availability(self):
        request = UpdateEmployeeRequest(available=False)

        self.service.update_employee_availability(
            employee_id="emp-123",
            update_employee_request=request,
        )

        self.mock_employee_repo.update_employee_availability.assert_called_once_with(
            employee_id="emp-123",
            available=False,
        )

    def test_delete_employee(self):
        employee = MagicMock()
        employee.email = "emp@test.com"

        self.mock_employee_repo.get_employee_by_id.return_value = employee

        self.service.delete_employee("emp-123")

        self.mock_employee_repo.delete_employee.assert_called_once_with(
            employee_id="emp-123",
            email="emp@test.com",
        )
