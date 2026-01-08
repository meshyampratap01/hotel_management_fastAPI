from fastapi import APIRouter, Depends, status

from dependencies import get_user_service, require_roles
from dtos.user_profile import UserProfileDTO
from models.roles import Role

router = APIRouter(prefix="/profile")


@router.get("/", status_code=status.HTTP_200_OK, response_model=UserProfileDTO)
def get_profile(
    current_user=Depends(
        require_roles(
            Role.MANAGER.value,
            Role.GUEST.value,
            Role.KITCHEN_STAFF.value,
            Role.CLEANING_STAFF.value,
        ),
    ),
    user_service=Depends(get_user_service),
):
    profile = user_service.get_profile(current_user.get("sub"))
    return profile
