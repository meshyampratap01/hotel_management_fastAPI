from typing import List

from boto3.dynamodb.conditions import Key
from app.app_exception.app_exception import AppException
from fastapi import Depends, status
from botocore.utils import ClientError
from app.dependencies import get_ddb_resource, get_table_name
from app.models.service_request import ServiceRequest, ServiceStatus


class ServiceRequestRepository:
    def __init__(
        self, ddb_resource=Depends(get_ddb_resource), table_name=Depends(get_table_name)
    ) -> None:
        self.table = ddb_resource.Table(table_name)
        self.table_name = table_name
        self.ddb_client = ddb_resource.meta.client

    def save_service_request(self, service_request: ServiceRequest) -> None:
        sk1 = f"Service#{service_request.status.value}#{service_request.id}"
        sk2 = f"Made#{service_request.status.value}#{service_request.id}"
        # print("service_request", service_request)

        try:
            self.ddb_client.transact_write_items(
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self.table_name,
                            "Item": {
                                "pk": "ServiceRequests",
                                "sk": sk1,
                                **service_request.model_dump(mode="json"),
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
                                **service_request.model_dump(mode="json"),
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

    def get_all_pending_service_requests(self) -> List[ServiceRequest]:
        try:
            response = self.table.query(
                KeyConditionExpression=Key("pk").eq("ServiceRequests")
                & Key("sk").begins_with("Service#Pending#")
            )

            items = response.get("Items", [])

            return [ServiceRequest(**item) for item in items]

        except ClientError:
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to fetch pending service requests",
            )

    def get_pending_service_requests_by_user_id(
        self, user_id: str
    ) -> List[ServiceRequest]:
        try:
            response = self.table.query(
                KeyConditionExpression=Key("pk").eq(f"User#{user_id}")
                & Key("sk").begins_with("Made#Pending#")
            )

            items = response.get("Items", [])

            return [ServiceRequest(**item) for item in items]

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
            print(response)

            item = response.get("Item")
            if not item:
                raise AppException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    message="Service request not found or not pending",
                )

            user_id = item["user_id"]
            print(user_id)
            print(employee_id)

            self.ddb_client.transact_write_items(
                TransactItems=[
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
                                "id": item["id"],
                                "user_id": item["user_id"],
                                "booking_id": item["booking_id"],
                                "room_num": int(item["room_num"]),
                                "type": item["type"],
                                "status": item["status"],
                                "is_assigned": item["is_assigned"],
                                "assigned_to": item["assigned_to"],
                                "details": item["details"],
                                "created_at": item["created_at"],
                            },
                            "ConditionExpression": "attribute_not_exists(pk)",
                        }
                    },
                ]
            )

        except ClientError as e:
            print(e.response)
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

    def get_assigned_service_requests(self, employee_id: str) -> List[ServiceRequest]:
        try:
            print("got into function")
            response = self.table.query(
                KeyConditionExpression=(
                    Key("pk").eq(f"User#{employee_id}")
                    & Key("sk").begins_with("Service#Pending#")
                )
            )

            items = response.get("Items", [])
            print(items)

            service_requests: List[ServiceRequest] = []

            for item in items:
                service_requests.append(ServiceRequest(**item))

            return service_requests

        except ClientError:
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to fetch assigned pending service requests",
            )

    def get_service_request_by_id(self, service_request_id: str) -> ServiceRequest:
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

            return ServiceRequest(**item)

        except ClientError:
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to fetch service request",
            )

    def update_service_request(
        self,
        service_request_id: str,
        update_status: ServiceStatus,
    ) -> None:
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
            employee_id = item.get("assigned_to")
            old_status = item["status"]

            new_sk_service = f"Service#{update_status.value}#{service_request_id}"
            new_sk_user = f"Made#{update_status.value}#{service_request_id}"

            transact_items = []

            transact_items.append(
                {
                    "Delete": {
                        "TableName": self.table_name,
                        "Key": {
                            "pk": "ServiceRequests",
                            "sk": f"Service#{old_status}#{service_request_id}",
                        },
                    }
                }
            )

            transact_items.append(
                {
                    "Put": {
                        "TableName": self.table_name,
                        "Item": {
                            **item,
                            "pk": "ServiceRequests",
                            "sk": new_sk_service,
                            "status": update_status.value,
                        },
                    }
                }
            )

            transact_items.append(
                {
                    "Delete": {
                        "TableName": self.table_name,
                        "Key": {
                            "pk": f"User#{user_id}",
                            "sk": f"Made#{old_status}#{service_request_id}",
                        },
                    }
                }
            )

            transact_items.append(
                {
                    "Put": {
                        "TableName": self.table_name,
                        "Item": {
                            **item,
                            "pk": f"User#{user_id}",
                            "sk": new_sk_user,
                            "status": update_status.value,
                        },
                    }
                }
            )

            if employee_id:
                transact_items.append(
                    {
                        "Delete": {
                            "TableName": self.table_name,
                            "Key": {
                                "pk": f"User#{employee_id}",
                                "sk": f"Service#{old_status}#{service_request_id}",
                            },
                        }
                    }
                )

                transact_items.append(
                    {
                        "Put": {
                            "TableName": self.table_name,
                            "Item": {
                                "pk": f"User#{employee_id}",
                                "sk": f"Service#{update_status.value}#{service_request_id}",
                                "service_request_id": service_request_id,
                                "user_id": user_id,
                                "room_num": item["room_num"],
                                "status": update_status.value,
                            },
                        }
                    }
                )

            self.ddb_client.transact_write_items(TransactItems=transact_items)

        except ClientError:
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to update service request status",
            )
