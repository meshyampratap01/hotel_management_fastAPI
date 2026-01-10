from boto3.dynamodb.conditions import Key
from botocore.utils import ClientError
from fastapi import Depends, status
from app.app_exception.app_exception import AppException
from app.dependencies import get_ddb_resource, get_table_name
from app.models import users


class UserRepository:
    def __init__(
        self,
        table_name=Depends(get_table_name),
        ddb_resource=Depends(get_ddb_resource),
    ) -> None:
        self.table = ddb_resource.Table(table_name)
        self.table_name = table_name
        self.ddb_client = ddb_resource.meta.client

    def save_user(self, user: users.User) -> None:
        try:
            self.ddb_client.transact_write_items(
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self.table_name,
                            "Item": {
                                "pk": f"User#{user.id}",
                                "sk": "PROFILE",
                                **user.model_dump(),
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
                    status_code=status.HTTP_409_CONFLICT, message="Email already exists"
                )
            raise AppException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to create user",
            )

    def get_user_by_email(self, email: str) -> users.User:
        try:
            email_resp = self.table.query(
                KeyConditionExpression=(
                    Key("pk").eq(f"Email#{email}") & Key("sk").eq("USER")
                ),
                Limit=1,
            )
        except ClientError:
            raise AppException(
                message="Failed to lookup email",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        items = email_resp.get("Items", [])
        if not items:
            raise AppException(
                message="User not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        user_id = items[0]["user_id"]

        try:
            user_resp = self.table.get_item(
                Key={
                    "pk": f"User#{user_id}",
                    "sk": "PROFILE",
                },
                ConsistentRead=True,
                ProjectionExpression="id, email, #name, password, #role, available",
                ExpressionAttributeNames={
                    "#name": "name",
                    "#role": "role",
                },
            )
        except ClientError:
            raise AppException(
                message="Failed to fetch user profile",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        item = user_resp.get("Item")
        if not item:
            raise AppException(
                message="User profile not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return users.User(**item)

    def get_user_by_id(self, user_id: str) -> users.User:
        try:
            user_resp = self.table.get_item(
                Key={
                    "pk": f"User#{user_id}",
                    "sk": "PROFILE",
                },
                ConsistentRead=True,
                ProjectionExpression="id, email, #name, password, #role, available",
                ExpressionAttributeNames={
                    "#name": "name",
                    "#role": "role",
                },
            )
        except ClientError:
            raise AppException(
                message="Failed to fetch user profile",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        item = user_resp.get("Item")
        if not item:
            raise AppException(
                message="User profile not found",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return users.User(
            **item,
        )
