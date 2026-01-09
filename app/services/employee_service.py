from typing import List
import uuid
from fastapi import Depends, status
from app_exception.app_exception import AppException
from dtos.employee_response import EmployeeResponseDTO
from models import users
from models.users import Role
from repository.employee_repository import EmployeeRepository
from dtos.employee_requests import CreateEmployeeRequest, UpdateEmployeeRequest
from utils import utils


class EmployeeService:
    def __init__(
        self, employee_repo: EmployeeRepository = Depends(EmployeeRepository)
    ) -> None:
        self.employee_repo = employee_repo

    def _create_employee(
        self,
        name: str,
        email: str,
        password: str,
        role: Role,
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

    def get_employees(self) -> List[EmployeeResponseDTO]:
        try:
            employees = self.employee_repo.get_employees()

            return [EmployeeResponseDTO(**e.model_dump(mode="json")) for e in employees]
        except Exception:
            raise

    def update_employee_availability(
        self, employee_id: str, update_employee_request: UpdateEmployeeRequest
    ):
        try:
            self.employee_repo.update_employee_availability(
                employee_id=employee_id, available=update_employee_request.available
            )
        except Exception:
            raise

    def delete_employee(self, employee_id: str):
        try:
            employee: users.User = self.employee_repo.get_employee_by_id(employee_id)

            self.employee_repo.delete_employee(
                employee_id=employee_id,
                email=employee.email,
            )
        except Exception:
            raise
