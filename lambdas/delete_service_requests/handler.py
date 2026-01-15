import boto3
import json

from letstayinn_package.service_request_repository import ServiceRequestRepository
from mypy_boto3_dynamodb import ServiceResource


def getddbresource():
    return boto3.resource("dynamodb")


def lambda_handler(event, context):
    ddb_resource: ServiceResource = getddbresource()
    service_request_repository: ServiceRequestRepository = ServiceRequestRepository(
        "letstayinn_fastapi", ddb_resource=ddb_resource
    )

    body = json.loads(event["Records"][0]["body"])
    booking_id = body["booking_id"]

    service_request_repository.delete_service_requests_by_booking(booking_id)

    return {
        "statusCode": 200,
        "body": "Success in deleting service requests",
    }
