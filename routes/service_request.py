from fastapi import APIRouter, Depends
from models.roles import Role
from dtos.service_request import CreateServiceRequest, assign_service_request_dto
from dependencies import get_service_request_service, require_roles
from services.service_request_service import ServiceRequestService

service_request_router = APIRouter(prefix="/service-requests")


@service_request_router.post("/")
def create_service_request(
    create_service_request: CreateServiceRequest,
    current_user=Depends(require_roles(Role.GUEST.value)),
    service_request_service: ServiceRequestService = Depends(
        get_service_request_service
    ),
):
    try:
        service_request_service.save_service_request(
            create_service_request, current_user
        )
        return {"detail": "service request successfully created"}
    except Exception:
        raise


@service_request_router.get("/")
def get_pending_service_request_by_role(
    current_user=Depends(require_roles(Role.MANAGER.value, Role.GUEST.value)),
    service_request_service: ServiceRequestService = Depends(
        get_service_request_service
    ),
):
    role = current_user.get("role")
    try:
        if role == Role.MANAGER.value:
            return service_request_service.get_all_pending_service_requests()
        elif role == Role.GUEST.value:
            return service_request_service.get_service_request_by_userID(current_user)
    except Exception:
        raise


@service_request_router.post("/assign/{service_request_id}")
def assign_service_request(
    request: assign_service_request_dto,
    service_request_id: str,
    _=Depends(require_roles(Role.MANAGER.value)),
    service_request_service: ServiceRequestService = Depends(
        get_service_request_service
    ),
):
    try:
        service_request_service.assign_service_request(
            service_request_id, request)
        return {"detail": "service request successfully assigned"}
    except Exception:
        raise
