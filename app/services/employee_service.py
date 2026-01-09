from typing import List
import uuid
from fastapi import Depends, status
from app_exception.app_exception import AppException
from dtos.employee_response import EmployeeResponseDTO
from models import users
from models.users import Role
from repository.employee_repository import EmployeeRepository
from dtos.employee_requests import CreateEmployeeRequest, UpdateEmployeeRequest
from utils import auth


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
            password=auth.hash_password(password),
            role=role,
            available=True,
        )

    def create_employee(self, create_employee_request: CreateEmployeeRequest) -> None:
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

        self.employee_repo.create_employee(new_emp)

    def get_employees(self) -> List[EmployeeResponseDTO]:
        employees = self.employee_repo.get_employees()

        return [EmployeeResponseDTO(**e.model_dump(mode="json")) for e in employees]

    def update_employee_availability(
        self, employee_id: str, update_employee_request: UpdateEmployeeRequest
    ) -> None:
        self.employee_repo.update_employee_availability(
            employee_id=employee_id, available=update_employee_request.available
        )

    def delete_employee(self, employee_id: str) -> None:
        employee: users.User = self.employee_repo.get_employee_by_id(employee_id)

        self.employee_repo.delete_employee(
            employee_id=employee_id,
            email=employee.email,
        )
