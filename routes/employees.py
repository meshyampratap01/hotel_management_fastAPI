from botocore.utils import email
from fastapi import APIRouter, Depends
from app_exception.app_exception import AppException
from dependencies import get_employee_service, require_roles
from models.roles import Role

from dtos.employee_requests import CreateEmployeeRequest, UpdateEmployeeRequest
from services.employee_service import EmployeeService

employee_router = APIRouter(prefix="/employees")


@employee_router.post("/")
def create_employee(
    create_employee_request: CreateEmployeeRequest,
    _=Depends(require_roles(Role.MANAGER.value)),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    try:
        employee_service.create_employee(create_employee_request)
        return {"detail": "employee created successfully"}
    except AppException:
        raise


@employee_router.get("/")
def get_employees(
    _=Depends(require_roles(Role.MANAGER.value)),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    try:
        return employee_service.get_employees()
    except Exception:
        raise


@employee_router.patch("/availability/{employee_id}")
def update_employee_availability(
    employee_id: str,
    request: UpdateEmployeeRequest,
    employee_service: EmployeeService = Depends(get_employee_service),
    _=Depends(
        require_roles(
            Role.MANAGER.value, Role.KITCHEN_STAFF.value, Role.CLEANING_STAFF.value
        )
    ),
):
    try:
        employee_service.update_employee_availability(employee_id, request)
        return {"detail": "employee successfully updated"}
    except Exception:
        raise


@employee_router.delete("/{employee_id}")
def delete_employee(
    employee_id: str,
    _=Depends(require_roles(Role.MANAGER)),
    employee_service: EmployeeService = Depends(get_employee_service),
):
    print("entered", employee_id)
    try:
        employee_service.delete_employee(employee_id)
        return {"detail": "employee deleted successfully"}
    except Exception:
        raise
