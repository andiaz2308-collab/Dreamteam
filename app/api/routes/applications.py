from fastapi import APIRouter, HTTPException

from app.schemas.application import ApplicationCreate
from app.services.applications.service import (
    ApplicationError,
    ApplicationService,
)


router = APIRouter(prefix="/api/applications", tags=["applications"])
service = ApplicationService()
service.seed_demo()


def _http_error(exc: ApplicationError) -> HTTPException:
    status_code = 404 if "no existe" in str(exc).lower() else 400
    return HTTPException(status_code=status_code, detail=str(exc))


@router.post("")
def create_application(payload: ApplicationCreate):
    application = service.create_and_queue(payload)
    return {"status": "success", "application": application.model_dump(mode="json")}


@router.get("")
def list_applications():
    return {
        "status": "success",
        "applications": [
            item.model_dump(mode="json") for item in service.list()
        ],
    }


@router.get("/stats")
def application_stats():
    return {"status": "success", "stats": service.stats().model_dump()}


@router.get("/{application_id}")
def get_application(application_id: str):
    try:
        application = service.get(application_id)
    except ApplicationError as exc:
        raise _http_error(exc) from exc
    return {"status": "success", "application": application.model_dump(mode="json")}


@router.post("/{application_id}/review")
def review_application(application_id: str):
    try:
        review = service.review(application_id)
    except ApplicationError as exc:
        raise _http_error(exc) from exc
    return {"status": "success", "review": review.model_dump(mode="json")}


@router.post("/{application_id}/retry")
def retry_application(application_id: str):
    try:
        application = service.retry(application_id)
    except ApplicationError as exc:
        raise _http_error(exc) from exc
    return {"status": "success", "application": application.model_dump(mode="json")}
