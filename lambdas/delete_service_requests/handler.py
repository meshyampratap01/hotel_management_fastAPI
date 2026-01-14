import boto3

from app.repository.service_request_repository import ServiceRequestRepository


def getddbresource():
    return boto3.resource("dynamodb")


def lambda_handler(event, context):
    ddb_resource = getddbresource()
    service_request_repository: ServiceRequestRepository = ServiceRequestRepository(
        ddb_resource, "letstayinn_fastapi"
    )

    service_request_repository.delete_service_requests_by_booking(event["booking_id"])

    return {
        "statusCode": 200,
        "body": "Success in deleting service requests",
    }
