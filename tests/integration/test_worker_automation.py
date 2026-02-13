import pytest

from src.workers.remediation_worker import RemediationWorker


@pytest.mark.asyncio
async def test_worker_start_and_shutdown():
    """
    Simple integration test for the remediation worker lifecycle.

    Verifies that the worker can start and then shut down cleanly without
    raising exceptions, using the real Redis/DB configuration provided in
    the test environment.
    """

    worker = RemediationWorker()

    # Start and immediately shut down the worker – this exercises the
    # Redis connection and engine disposal logic.
    await worker.start()
    await worker.shutdown(reason="test")
