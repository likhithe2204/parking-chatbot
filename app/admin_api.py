import os
import secrets
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app import admin_store
from app.config import ADMIN_DB_PATH
from app.reservation import DATETIME_FORMAT, validate_reservation

load_dotenv()


class ReservationIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    car_number: str = Field(min_length=1, max_length=20)
    start: str = Field(min_length=1, max_length=20)
    end: str = Field(min_length=1, max_length=20)
    note: str = Field(default="", max_length=1000)


class DecisionIn(BaseModel):
    decision: Literal["APPROVED", "REFUSED"]
    reason: str = Field(default="", max_length=500)


def create_app(db_path=None, api_key: str | None = None) -> FastAPI:
    key = api_key or os.environ.get("ADMIN_API_KEY", "")
    if not key:
        raise RuntimeError("ADMIN_API_KEY is not set")
    path = Path(db_path) if db_path else ADMIN_DB_PATH

    api = FastAPI(title="Parking Admin Service")

    def require_key(x_api_key: str = Header(default="")) -> None:
        if not secrets.compare_digest(x_api_key.encode(), key.encode()):
            raise HTTPException(status_code=401, detail="Invalid or missing API key")

    @api.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @api.post("/requests", status_code=201, dependencies=[Depends(require_key)])
    def create_request(body: ReservationIn) -> dict:
        valid, errors = validate_reservation(
            body.first_name, body.last_name, body.car_number, body.start, body.end
        )
        if errors:
            raise HTTPException(status_code=422, detail=errors)
        return admin_store.create_request(
            valid.first_name,
            valid.last_name,
            valid.car_number,
            valid.start.strftime(DATETIME_FORMAT),
            valid.end.strftime(DATETIME_FORMAT),
            body.note,
            path,
        )

    @api.get("/requests", dependencies=[Depends(require_key)])
    def list_requests(
        status: Literal["PENDING", "APPROVED", "REFUSED"] | None = None,
    ) -> list[dict]:
        return admin_store.list_requests(status, path)

    @api.get("/requests/{request_id}", dependencies=[Depends(require_key)])
    def get_request(request_id: str) -> dict:
        record = admin_store.get_request(request_id, path)
        if record is None:
            raise HTTPException(status_code=404, detail="Request not found")
        return record

    @api.post("/requests/{request_id}/decision", dependencies=[Depends(require_key)])
    def decide(request_id: str, body: DecisionIn) -> dict:
        try:
            return admin_store.decide(request_id, body.decision, body.reason, path)
        except admin_store.RequestNotFound:
            raise HTTPException(status_code=404, detail="Request not found")
        except admin_store.AlreadyDecided:
            raise HTTPException(status_code=409, detail="Request was already decided")

    return api