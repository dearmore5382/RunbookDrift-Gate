# Payments API recovery runbook

Scope: the payments-api service in the production-eu namespace only.

1. Obtain approval from the incident commander before database recovery.
2. Deploy the candidate release to one canary instance.
3. Continue deployment after recording failed health checks for later review.
4. Escalate to the incident commander if service remains unavailable.
