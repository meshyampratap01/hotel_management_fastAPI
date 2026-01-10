from typing import List
from boto3.dynamodb.conditions import Key
from app.dependencies import get_ddb_resource, get_table_name
from app.models.feedbacks import Feedback
from botocore.utils import ClientError
from app.app_exception.app_exception import AppException
from fastapi import Depends, status


class FeedbackRepository:
    def __init__(
        self, ddb_resource=Depends(get_ddb_resource), table_name=Depends(get_table_name)
    ):
        self.table = ddb_resource.Table(table_name)
        self.table_name = table_name
        self.ddb_client = ddb_resource.meta.client

    def save_feedback(self, feedback: Feedback) -> None:
        try:
            self.table.put_item(
                Item={
                    **feedback.model_dump(mode="json"),
                    "pk": "Feedbacks",
                    "sk": f"Feedback#{feedback.id}",
                }
            )
        except ClientError:
            raise AppException(
                message="Failed to save feedback",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_all_feedbacks(self) -> List[Feedback]:
        try:
            feedback_items = self.table.query(
                KeyConditionExpression=Key("pk").eq("Feedbacks")
                & Key("sk").begins_with("Feedback#")
            ).get("Items", [])
            return [Feedback(**item) for item in feedback_items]
        except ClientError:
            raise AppException(
                message="Failed to fetch feedbacks",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete_feedback(self, feedback_id: str) -> None:
        try:
            self.table.delete_item(
                Key={
                    "pk": "Feedbacks",
                    "sk": f"Feedback#{feedback_id}",
                }
            )
        except ClientError:
            raise AppException(
                message="Failed to delete feedback",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
