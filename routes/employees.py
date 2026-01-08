from fastapi import APIRouter, Depends
from app_exception.app_exception import AppException
from dependencies import (
    require_roles,
)
from dtos.service_request import (
    AssignedPendingServiceRequestDTO,
    UpdateServiceRequestStatus,
)
from models.users import Role

from dtos.employee_requests import CreateEmployeeRequest, UpdateEmployeeRequest
from services.employee_service import EmployeeService
from services.service_request_service import ServiceRequestService

employee_router = APIRouter(prefix="/employees")


@employee_router.post("/")
def create_employee(
    create_employee_request: CreateEmployeeRequest,
    _=Depends(require_roles(Role.MANAGER.value)),
    employee_service: EmployeeService = Depends(EmployeeService),
):
    try:
        employee_service.create_employee(create_employee_request)
        return {"detail": "employee created successfully"}
    except AppException:
        raise


@employee_router.get("/")
def get_employees(
    _=Depends(require_roles(Role.MANAGER.value)),
    employee_service: EmployeeService = Depends(EmployeeService),
):
    try:
        return employee_service.get_employees()
    except Exception:
        raise


@employee_router.patch("/availability/{employee_id}")
def update_employee_availability(
    employee_id: str,
    request: UpdateEmployeeRequest,
    employee_service: EmployeeService = Depends(EmployeeService),
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
    employee_service: EmployeeService = Depends(EmployeeService),
):
    print("entered", employee_id)
    try:
        employee_service.delete_employee(employee_id)
        return {"detail": "employee deleted successfully"}
    except Exception:
        raise


@employee_router.get(
    "/service-requests", response_model=list[AssignedPendingServiceRequestDTO]
)
def get_assigned_service_request(
    current_user=Depends(
        require_roles(Role.KITCHEN_STAFF.value, Role.CLEANING_STAFF.value)
    ),
    service_reqeust_service: ServiceRequestService = Depends(
        ServiceRequestService),
):
    try:
        return service_reqeust_service.get_assigned_service_requests(current_user)
    except Exception:
        raise


@employee_router.put("/service-requests/status/{service_request_id}")
def update_service_request_status(
    service_request_id: str,
    request: UpdateServiceRequestStatus,
    _=Depends(require_roles(Role.KITCHEN_STAFF.value,
              Role.CLEANING_STAFF.value)),
    service_reqeust_service: ServiceRequestService = Depends(
        ServiceRequestService),
):
    try:
        return service_reqeust_service.update_service_request(
            service_request_id, request
        )
    except Exception:
        raise
