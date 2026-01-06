from fastapi import APIRouter, Depends
from app_exception.app_exception import AppException
from dependencies import get_employee_service, require_roles
from models.roles import Role

from dtos.employee_requests import CreateEmployeeRequest
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
