from fastapi import APIRouter, Depends, status
from app.dependencies import (
    require_roles,
)
from app.response.response import APIResponse
from app.dtos.service_request import (
    UpdateServiceRequestStatus,
)
from app.models.users import Role

from app.dtos.employee_requests import CreateEmployeeRequest, UpdateEmployeeRequest
from app.services.employee_service import EmployeeService
from app.services.service_request_service import ServiceRequestService

employee_router = APIRouter(prefix="/employees")


@employee_router.post(
    "/", response_model=APIResponse, status_code=status.HTTP_201_CREATED
)
def create_employee(
    create_employee_request: CreateEmployeeRequest,
    _=Depends(require_roles(Role.MANAGER.value)),
    employee_service: EmployeeService = Depends(EmployeeService),
):
    employee_service.create_employee(create_employee_request)
    return APIResponse(
        status_code=status.HTTP_201_CREATED,
        message="Employee created successfully",
    )


@employee_router.get("/", response_model=APIResponse, status_code=status.HTTP_200_OK)
def get_employees(
    _=Depends(require_roles(Role.MANAGER.value)),
    employee_service: EmployeeService = Depends(EmployeeService),
):
    employees = employee_service.get_employees()
    return APIResponse(
        status_code=status.HTTP_200_OK,
        message="Employees Fetched Successfully",
        data=employees,
    )


@employee_router.patch(
    "/availability/{employee_id}",
    status_code=status.HTTP_200_OK,
    response_model=APIResponse,
)
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
    employee_service.update_employee_availability(employee_id, request)
    return APIResponse(
        status_code=status.HTTP_200_OK,
        message="Employee availability updated successfully",
    )


@employee_router.delete(
    "/{employee_id}", status_code=status.HTTP_200_OK, response_model=APIResponse
)
def delete_employee(
    employee_id: str,
    _=Depends(require_roles(Role.MANAGER)),
    employee_service: EmployeeService = Depends(EmployeeService),
):
    employee_service.delete_employee(employee_id)
    return APIResponse(
        status_code=status.HTTP_200_OK,
        message="Employee deleted successfully",
    )


@employee_router.get(
    "/service-requests", response_model=APIResponse, status_code=status.HTTP_200_OK
)
def get_assigned_service_request(
    current_user=Depends(
        require_roles(Role.KITCHEN_STAFF.value, Role.CLEANING_STAFF.value)
    ),
    service_reqeust_service: ServiceRequestService = Depends(ServiceRequestService),
):
    requests = service_reqeust_service.get_assigned_service_requests(current_user)
    return APIResponse(
        status_code=status.HTTP_200_OK,
        message="Service requests fetched successfully",
        data=requests,
    )


@employee_router.put(
    "/service-requests/status/{service_request_id}",
    status_code=status.HTTP_200_OK,
    response_model=APIResponse,
)
def update_service_request_status(
    service_request_id: str,
    request: UpdateServiceRequestStatus,
    _=Depends(require_roles(Role.KITCHEN_STAFF.value, Role.CLEANING_STAFF.value)),
    service_reqeust_service: ServiceRequestService = Depends(ServiceRequestService),
):
    service_reqeust_service.update_service_request(service_request_id, request)
    return APIResponse(
        status_code=status.HTTP_200_OK,
        message="Service request status updated successfully",
    )
