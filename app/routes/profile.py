from fastapi import APIRouter, Depends, status

from app.response.response import APIResponse
from app.services.user_service import UserService
from app.dependencies import require_roles
from app.dtos.user_profile import UserProfileDTO
from app.models.users import Role

router = APIRouter(prefix="/profile")


@router.get("/", status_code=status.HTTP_200_OK, response_model=APIResponse)
def get_profile(
    current_user=Depends(
        require_roles(
            Role.MANAGER.value,
            Role.GUEST.value,
            Role.KITCHEN_STAFF.value,
            Role.CLEANING_STAFF.value,
        ),
    ),
    user_service: UserService = Depends(UserService),
):
    profile: UserProfileDTO = user_service.get_profile(current_user.get("sub"))
    return APIResponse(
        status_code=status.HTTP_200_OK,
        message="Profile Fetched Successfully",
        data=profile,
    )
