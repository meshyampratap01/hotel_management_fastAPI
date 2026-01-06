from abc import ABC, abstractmethod
from typing import List

from boto3.dynamodb.conditions import Key
from botocore.utils import ClientError
from fastapi import status

from app_exception.app_exception import AppException
from models import users


class EmployeeRepository(ABC):
    @abstractmethod
    def create_employee(self, user: users.User) -> None:
        pass

    @abstractmethod
    def get_employees(self) -> List[users.User]:
        pass


class DDBEmployeeRepository(EmployeeRepository):
    def __init__(self, ddb_resource, table_name) -> None:
        self.table = ddb_resource.Table(table_name)
        self.table_name = table_name
        self.ddb_client = ddb_resource.meta.client

    def create_employee(self, user: users.User) -> None:
        try:
            self.ddb_client.transact_write_items(
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self.table_name,
                            "Item": {
                                "pk": f"User#{user.id}",
                                "sk": "PROFILE",
                                "id": user.id,
                                "email": user.email,
                                "name": user.name,
                                "password": user.password,
                                "role": user.role,
                                "available": user.available,
                            },
                        }
                    },
                    {
                        "Put": {
                            "TableName": self.table_name,
                            "Item": {
                                "pk": f"Email#{user.email}",
                                "sk": "USER",
                                "user_id": user.id,
                            },
                            "ConditionExpression": "attribute_not_exists(pk)",
                        }
                    },
                    {
                        "Put": {
                            "TableName": self.table_name,
                            "Item": {
                                "pk": "Employee",
                                "sk": f"Employee#{user.id}",
                                "id": user.id,
                                "email": user.email,
                                "name": user.name,
                                "role": user.role,
                                "available": user.available,
                            },
                        }
                    },
                ]
            )

        except ClientError as e:
            if e.response.get("Error", {}).get(
                "Code"
            ) == "TransactionCanceledException" and any(
                r.get("Code") == "ConditionalCheckFailed"
                for r in e.response.get("CancellationReasons", [])
            ):
                raise AppException(
                    status_code=status.HTTP_409_CONFLICT,
                    message="Email already exists",
                )

            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to create employee",
            )

    def get_employees(self) -> List[users.User]:
        try:
            response = self.table.query(
                KeyConditionExpression=Key("pk").eq("Employee"))

            items = response.get("Items", [])

            employees: list[users.User] = []

            for item in items:
                employees.append(
                    users.User(
                        id=item["id"],
                        name=item["name"],
                        email=item["email"],
                        password="",
                        role=item["role"],
                        available=item["available"],
                    )
                )

            return employees

        except ClientError:
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to fetch employees",
            )
