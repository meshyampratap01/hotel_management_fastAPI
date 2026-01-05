from enum import Enum


class Role(str, Enum):
    GUEST = "Guest"
    KITCHEN_STAFF = "KitchenStaff"
    CLEANING_STAFF = "CleaningStaff"
    MANAGER = "Manager"
