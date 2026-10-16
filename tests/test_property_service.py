from datetime import date

from src.property_service import PropertyWorkflow, TenantDocument


def test_expired_document_is_rejected_and_grouped():
    captured = []
    workflow = PropertyWorkflow(lambda **payload: captured.append(payload) or {})

    result = workflow.submit_document(TenantDocument("doc-1", "tenant-1", date(2020, 1, 1)))

    assert result == "document_rejected"
    assert captured[0]["fingerprint"] == ["property-management", "document-validation"]
    assert captured[0]["context"]["tenant_id"] == "tenant-1"

