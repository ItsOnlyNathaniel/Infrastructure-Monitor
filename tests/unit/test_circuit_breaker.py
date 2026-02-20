# immports
import asyncio
from src.core.circuit_breaker import CircuitBreaker

async def test_circuit_breaker_opens_after_threshold():
    cb = CircuitBreaker(max_retry_attempts=3)

    # Should allow attempts while closed
    can_attempt, _ = await cb.can_attempt_remediation("i-123", "ec2")
    assert can_attempt is True

    # Record 3 failures
    await cb.failed_attempt("i-123", "ec2")
    await cb.failed_attempt("i-123", "ec2")
    await cb.failed_attempt("i-123", "ec2")

    # Now should be blocked
    can_attempt, reason = await cb.can_attempt_remediation("i-123", "ec2")
    assert can_attempt is False
    assert "Circuit breaker open" in reason

async def test_circuit_recovers_after_timeout():
    cb = CircuitBreaker(max_retry_attempts=2, remediation_timeout=1)

    # Trip circuit
    await cb.failed_attempt("i-123", "ec2")
    await cb.failed_attempt("i-123", "ec2")

    # Should be open
    state = await cb.get_state("i-123", "ec2")
    assert state == "open"

    # Wait for timeout
    await asyncio.sleep(1.5)

    # Should transition to half_open
    state = await cb.get_state("i-123", "ec2")
    assert state == "half_open"
