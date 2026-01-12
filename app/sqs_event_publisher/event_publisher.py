import json
import boto3
from datetime import datetime, timezone

from botocore.utils import ClientError
from fastapi import Depends, status

from app.app_exception.app_exception import AppException
from app.dependencies import get_queue_url


class BookingEventPublisher:
    def __init__(self, queue_url=Depends(get_queue_url)):
        self.sqs = boto3.client("sqs")
        self.queue_url = queue_url

    def publish_booking_cancelled(self, booking):
        message = {
            "event_type": "BOOKING_CANCELLED",
            "booking_id": booking.id,
            "food_req": booking.food_req,
            "clean_req": booking.clean_req,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message),
            )
        except ClientError as e:
            raise AppException(
                message=f"Failed to send message to SQS and the response is {e.response}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
