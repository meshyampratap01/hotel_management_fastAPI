from models import rooms


def get_all_rooms(room_repo) -> list[rooms.Room]:
    try:
        rooms = room_repo.get_all_rooms()
        return rooms
    except Exception:
        raise


def get_available_rooms(room_repo) -> list[rooms.Room]:
    try:
        rooms = room_repo.get_available_rooms()
        return rooms
    except Exception:
        raise
