from abc import ABC, abstractmethod
from typing import List

from boto3.dynamodb.conditions import Key
from app_exception.app_exception import AppException
from fastapi import status
from botocore.utils import ClientError
from models.service_request import ServiceRequest, ServiceStatus, ServiceType


class ServiceRequestRepository(ABC):
    @abstractmethod
    def save_service_request(self, service_request):
        pass

    @abstractmethod
    def get_all_pending_service_requests(self) -> List[ServiceRequest]:
        pass

    @abstractmethod
    def get_pending_service_requests_by_user_id(self, user_id) -> List[ServiceRequest]:
        pass

    @abstractmethod
    def assign_service_request(self, service_request_id, employee_id):
        pass


class DDBServiceRequestRepository(ServiceRequestRepository):
    def __init__(self, ddb_resource, table_name) -> None:
        self.table = ddb_resource.Table(table_name)
        self.table_name = table_name
        self.ddb_client = ddb_resource.meta.client

    def _map_item_to_service_request(self, item: dict) -> ServiceRequest:
        return ServiceRequest(
            id=item["id"],
            user_id=item["user_id"],
            booking_id=item["booking_id"],
            room_num=int(item["room_num"]),
            type=ServiceType(item["type"]),
            status=ServiceStatus(item["status"]),
            is_assigned=item.get("is_assigned", False),
            assigned_to=item.get("assigned_to"),
            details=item["details"],
        )

    def save_service_request(self, service_request: ServiceRequest):
        # if service_request.status != ServiceStatus.PENDING:
        #     raise ValueError("New service requests must start in PENDING state")
        sk1 = f"Service#{service_request.status.value}#{service_request.id}"
        sk2 = f"Made#{service_request.status.value}#{service_request.id}"

        try:
            self.ddb_client.transact_write_items(
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self.table_name,
                            "Item": {
                                "pk": "ServiceRequests",
                                "sk": sk1,
                                "id": service_request.id,
                                "user_id": service_request.user_id,
                                "booking_id": service_request.booking_id,
                                "room_num": service_request.room_num,
                                "type": service_request.type.value,
                                "status": service_request.status.value,
                                "is_assigned": service_request.is_assigned,
                                "assigned_to": service_request.assigned_to,
                                "details": service_request.details,
                            },
                            "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
                        }
                    },
                    {
                        "Put": {
                            "TableName": self.table_name,
                            "Item": {
                                "pk": f"User#{service_request.user_id}",
                                "sk": sk2,
                                "user_id": service_request.user_id,
                                "id": service_request.id,
                                "booking_id": service_request.booking_id,
                                "room_num": service_request.room_num,
                                "type": service_request.type.value,
                                "is_assigned": service_request.is_assigned,
                                "assigned_to": service_request.assigned_to,
                                "status": service_request.status.value,
                                "details": service_request.details,
                            },
                            "ConditionExpression": "attribute_not_exists(pk) AND attribute_not_exists(sk)",
                        }
                    },
                ]
            )

        except ClientError as e:
            error = e.response.get("Error", {})
            code = error.get("Code")

            if code == "TransactionCanceledException":
                reasons = e.response.get("CancellationReasons", [])

                if any(r.get("Code") == "ConditionalCheckFailed" for r in reasons):
                    raise AppException(
                        status_code=status.HTTP_409_CONFLICT,
                        message="Booking already exists",
                    )

            raise AppException(
                message="Failed to create service request",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_all_pending_service_requests(self):
        try:
            response = self.table.query(
                KeyConditionExpression=Key("pk").eq("ServiceRequests")
                & Key("sk").begins_with("Service#Pending#")
            )

            items = response.get("Items", [])

            return [self._map_item_to_service_request(item) for item in items]

        except ClientError:
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to fetch pending service requests",
            )

    def get_pending_service_requests_by_user_id(self, user_id: str):
        try:
            response = self.table.query(
                KeyConditionExpression=Key("pk").eq(f"User#{user_id}")
                & Key("sk").begins_with("Made#Pending#")
            )

            items = response.get("Items", [])

            return [self._map_item_to_service_request(item) for item in items]

        except ClientError:
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to fetch user's pending service requests",
            )

    def assign_service_request(self, service_request_id: str, employee_id: str):
        try:
            response = self.table.get_item(
                Key={
                    "pk": "ServiceRequests",
                    "sk": f"Service#Pending#{service_request_id}",
                }
            )

            item = response.get("Item")
            if not item:
                raise AppException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Service request not found or not pending",
                )

            user_id = item["user_id"]

            self.ddb_client.transact_write_items(
                TransactItems=[
                    # 1️⃣ Update manager view
                    {
                        "Update": {
                            "TableName": self.table_name,
                            "Key": {
                                "pk": "ServiceRequests",
                                "sk": f"Service#Pending#{service_request_id}",
                            },
                            "UpdateExpression": """
                                SET is_assigned = :true,
                                    assigned_to = :emp
                            """,
                            "ConditionExpression": "attribute_exists(pk) AND is_assigned = :false",
                            "ExpressionAttributeValues": {
                                ":true": True,
                                ":false": False,
                                ":emp": employee_id,
                            },
                        }
                    },
                    # 2️⃣ Update user view
                    {
                        "Update": {
                            "TableName": self.table_name,
                            "Key": {
                                "pk": f"User#{user_id}",
                                "sk": f"Made#Pending#{service_request_id}",
                            },
                            "UpdateExpression": """
                                SET is_assigned = :true,
                                    assigned_to = :emp
                            """,
                            "ConditionExpression": "attribute_exists(pk)",
                            "ExpressionAttributeValues": {
                                ":true": True,
                                ":emp": employee_id,
                            },
                        }
                    },
                    {
                        "Put": {
                            "TableName": self.table_name,
                            "Item": {
                                "pk": f"User#{employee_id}",
                                "sk": f"Service#Pending#{service_request_id}",
                                "service_request_id": service_request_id,
                                "user_id": user_id,
                                "room_num": item["room_num"],
                                "status": item["status"],
                            },
                            "ConditionExpression": "attribute_not_exists(pk)",
                        }
                    },
                ]
            )

        except ClientError as e:
            code = e.response.get("Error", {}).get("Code")

            if code == "TransactionCanceledException":
                raise AppException(
                    status_code=status.HTTP_409_CONFLICT,
                    message="Service request already assigned or state changed",
                )

            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to assign service request",
            )
