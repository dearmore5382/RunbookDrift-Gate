# Payments API recovery runbook

Scope: the payments-api service in the production-eu namespace only.

1. Obtain approval from the incident commander before database recovery.
2. Deploy the candidate release to one canary instance.
3. Stop the deployment immediately if health checks fail.
4. Roll back to the previous signed release.
5. Verify error rate is below 1% for ten minutes after rollback.
6. Escalate to the incident commander if recovery does not restore service.
