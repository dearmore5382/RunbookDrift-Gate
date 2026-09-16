# Payments API recovery runbook

Scope: only payments-api in the production-eu namespace.

1. Database recovery requires incident-commander approval.
2. Release first to a single canary.
3. Halt immediately when a health check fails.
4. Restore the preceding signed release.
5. Confirm the error rate remains under 1% for ten minutes after restoration.
6. Notify and escalate to the incident commander if service is not restored.
