# Production recovery runbook

Scope: every service and database in all production namespaces.

1. Obtain approval from the incident commander before database recovery.
2. Deploy the candidate release to one canary instance per service.
3. Stop deployment if health checks fail and roll back to each previous signed release.
4. Verify every service error rate remains below 1% for ten minutes.
