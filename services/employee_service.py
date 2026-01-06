from typing import List
import uuid
from fastapi import status
from app_exception.app_exception import AppException
from dtos.employee_response import EmployeeResponse
from models import users
from models.roles import Role
from repository.employee_repository import EmployeeRepository
from dtos.employee_requests import CreateEmployeeRequest
from utils import utils


class EmployeeService:
    def __init__(self, employee_repo: EmployeeRepository) -> None:
        self.employee_repo = employee_repo

    def _create_employee(
        self,
        name: str,
        email: str,
        password: str,
        role: str,
    ) -> users.User:
        return users.User(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            password=utils.hash_password(password),
            role=role,
            available=True,
        )

    def create_employee(self, create_employee_request: CreateEmployeeRequest):
        emp_role = create_employee_request.role

        if emp_role not in {Role.KITCHEN_STAFF, Role.CLEANING_STAFF, Role.MANAGER}:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid role for employee",
            )

        new_emp = self._create_employee(
            create_employee_request.name,
            create_employee_request.email,
            create_employee_request.password,
            create_employee_request.role,
        )

        try:
            self.employee_repo.create_employee(new_emp)
        except Exception:
            raise

    def get_employees(self) -> List[EmployeeResponse]:
        try:
            employees = self.employee_repo.get_employees()

            return [
                EmployeeResponse(
                    id=e.id,
                    name=e.name,
                    email=e.email,
                    role=e.role,
                    available=e.available,
                )
                for e in employees
            ]
        except Exception:
            raise
