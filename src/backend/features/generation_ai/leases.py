from datetime import timedelta

# Fixed execution lease, deliberately longer than the worker's 180s job timeout.
# No heartbeat: a provider that outlives this deadline loses apply ownership.
RUNNING_LEASE = timedelta(minutes=10)
RUNNING_RECOVERY_PAGE_SIZE = 100
