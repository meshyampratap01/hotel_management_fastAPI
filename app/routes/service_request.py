from fastapi import APIRouter, Depends, status
from app.response.response import APIResponse
from app.models.users import Role
from app.dtos.service_request import CreateServiceRequest, assign_service_request_dto
from app.dependencies import require_roles
from app.services.service_request_service import ServiceRequestService

service_request_router = APIRouter(prefix="/service-requests")


@service_request_router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=APIResponse
)
def create_service_request(
    create_service_request: CreateServiceRequest,
    current_user=Depends(require_roles(Role.GUEST.value)),
    service_request_service: ServiceRequestService = Depends(ServiceRequestService),
):
    service_request_service.save_service_request(create_service_request, current_user)
    return APIResponse(
        status_code=status.HTTP_201_CREATED,
        message="Service request created successfully",
    )


@service_request_router.get(
    "/", status_code=status.HTTP_200_OK, response_model=APIResponse
)
def get_pending_service_request_by_role(
    current_user=Depends(require_roles(Role.MANAGER.value, Role.GUEST.value)),
    service_request_service: ServiceRequestService = Depends(ServiceRequestService),
):
    role = current_user.get("role")
    if role == Role.MANAGER.value:
        requests = service_request_service.get_all_pending_service_requests()
        return APIResponse(
            status_code=status.HTTP_200_OK,
            message="Service requests fetched successfully",
            data=requests,
        )
    elif role == Role.GUEST.value:
        requests = service_request_service.get_service_request_by_userID(current_user)
        return APIResponse(
            status_code=status.HTTP_200_OK,
            message="Service requests fetched successfully",
            data=requests,
        )


@service_request_router.post(
    "/assign/{service_request_id}",
    status_code=status.HTTP_200_OK,
    response_model=APIResponse,
)
def assign_service_request(
    request: assign_service_request_dto,
    service_request_id: str,
    _=Depends(require_roles(Role.MANAGER.value)),
    service_request_service: ServiceRequestService = Depends(ServiceRequestService),
):
    service_request_service.assign_service_request(service_request_id, request)
    return APIResponse(
        status_code=status.HTTP_200_OK,
        message="Service request assigned successfully",
    )
