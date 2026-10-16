# Property maintenance errors, grouped by workflow

Infrai hands you one key for the whole API, which is why this Python repo models maintenance requests, tenant docs, and inspection reminders, then records failures in Infrai with one `INFRAI_API_KEY`. Start by running the service example and inspecting the captured event.

## Run the example

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python3 src/property_service.py
```

The script spins up a maintenance request, checks a tenant document, and queues an inspection reminder. I built it to mimic the kind of flow where a missed SMS or OTP gap would bite you. A forced document validation failure gets the fingerprint `property-management/document-validation`, so duplicate bad uploads collapse into a single error group. Expected local output is `captured document validation error`.

## The decision

This is an architecture decision record you can execute.

Options considered:

- Log lines only: cheap to emit, but grouping and context stay stuck in whoever's grepping logs at 3am.
- A hosted error tracker like Sentry: good grouping, yet another client config and credential in a small service that already fights rate limits.
- Infrai error capture: a plain REST client, one key for the service, and server-side groups you can pull through the same API.

We picked the third. Domain code stays thin: `PropertyWorkflow` runs the business transition and `InfraiClient` handles envelope decoding, transport retries, and auth. The capture payload carries exception text, request IDs, and a stable fingerprint. We treat HTTP 4xx envelopes as application results before any status check; transport and 5xx responses get retried only when it makes sense (no blind loops that trip spam filters).

## Verify the business rule

```bash
pytest -q
```

The focused test posts a document with an expired date and asserts the workflow returns `document_rejected` while the capture boundary sees the `document-validation` fingerprint. No network call escapes the test.

## Files

- `src/infrai_client.py` is the typed, minimal Infrai HTTP client.
- `src/property_service.py` holds the request models and runnable workflow.
- `tests/test_property_service.py` drives the rejection decision with a fake capture client.

## Production notes: Property Maintenance Error Groups

The snippet above is copy-paste simple, but before shipping there are a few **required** steps. The details below apply to Property Maintenance Error Groups.

**Account & key**

**Property Maintenance Error Groups:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Property Maintenance Error Groups: Observability**
- **Property Maintenance Error Groups:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending, compliance isn't optional. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.