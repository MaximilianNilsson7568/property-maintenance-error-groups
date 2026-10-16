from __future__ import annotations

import traceback
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

try:
    from src.infrai_client import InfraiClient, errors
except ModuleNotFoundError:  # direct `python3 src/property_service.py`
    from infrai_client import InfraiClient, errors


@dataclass(frozen=True)
class MaintenanceRequest:
    request_id: str
    property_id: str
    tenant_id: str
    summary: str


@dataclass(frozen=True)
class TenantDocument:
    document_id: str
    tenant_id: str
    expires_on: date


@dataclass(frozen=True)
class InspectionReminder:
    property_id: str
    due_on: date


class PropertyWorkflow:
    def __init__(self, capture: Callable[..., dict[str, Any]]):
        self._capture = capture

    def submit_document(self, document: TenantDocument) -> str:
        try:
            if document.expires_on < date.today():
                raise ValueError("tenant document has expired")
            return "document_accepted"
        except Exception as exc:
            self._capture(
                title="tenant document validation failed",
                message=str(exc),
                level="error",
                fingerprint=["property-management", "document-validation"],
                exception=traceback.format_exc(),
                context={"document_id": document.document_id, "tenant_id": document.tenant_id},
            )
            return "document_rejected"

    def create_request(self, request: MaintenanceRequest) -> str:
        if not request.summary.strip():
            raise ValueError("maintenance request summary is required")
        return "request_created"

    def schedule_inspection(self, reminder: InspectionReminder) -> str:
        return "inspection_scheduled"


def main() -> None:
    workflow = PropertyWorkflow(errors(InfraiClient()).capture)
    workflow.create_request(MaintenanceRequest("mr-100", "building-7", "tenant-4", "Leaking faucet"))
    result = workflow.submit_document(TenantDocument("doc-9", "tenant-4", date(2020, 1, 1)))
    workflow.schedule_inspection(InspectionReminder("building-7", date(2026, 10, 1)))
    if result == "document_rejected":
        print("captured document validation error")


if __name__ == "__main__":
    main()
