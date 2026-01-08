from fastapi import APIRouter, Depends, status

from services.user_service import UserService
from dependencies import require_roles
from dtos.user_profile import UserProfileDTO
from models.users import Role

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
    user_service: UserService = Depends(UserService),
):
    profile = user_service.get_profile(current_user.get("sub"))
    return profile
