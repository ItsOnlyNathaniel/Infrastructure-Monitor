# Imports
import logging
from datetime import datetime
from typing import Literal
from src.core.config import settings
from src.core.redis_client import redis_client

""" Prevents remediation loops by tracking failure patterns """

logger = logging.getLogger(__name__)
CircuitState = Literal["closed","open","testing"]

class CircuitBreaker:

    def __init__(
        self,
        health_check_interval = settings.health_check_interval,
        max_retry_attempts = settings.max_retry_attempts,
        remediation_timeout = settings.remediation_timeout,
    ):
        self.health_check_interval = health_check_interval
        self.remediation_timeout = remediation_timeout
        self.max_retry_attempts = max_retry_attempts

    def get_redis_keys(self, resource_id: str, resource_type: str):
        """Generate Redis keys for this resource"""
        prefix = f"circuit_breaker:{resource_type}:{resource_id}"
        return {
            "state": f"{prefix}:state",
            "failures": f"{prefix}:failures",
            "successes": f"{prefix}:successes",
            "last_failure_time": f"{prefix}:last_failure",
            "opened_at": f"{prefix}:opened_at",
        }

    async def get_state(self, resource_id: str, resource_type: str) -> CircuitState:
        keys = self.get_redis_keys(resource_id, resource_type)
        state = await redis_client.get(keys["state"])
        if not state:
            return "closed"

        if state == "open":
            opened_at = await redis_client.get(keys["opened_at"])
            if opened_at:
                opened_time = float(opened_at)
                if datetime.now().timestamp() - opened_time >= self.remediation_timeout:
                    await self.set_state(resource_id, resource_type, "testing")
                    logger.info("Circuit transitioned to testing",
                        extra={"resource_id": resource_id, "resource_type": resource_type,"timeout_seconds": self.remediation_timeout,
                        }
                    )
                    return "testing"
        return state

    async def set_state(self, resource_id: str, resource_type: str, state: CircuitState):
        keys = self.get_redis_keys(resource_id, resource_type)
        await redis_client.set(keys["state"], state, ttl=3600)

        if state == "open":
            await redis_client.set(keys["opened_at"], str(datetime.now().timestamp()), ttl=3600)

    async def can_attempt_remediation(self, resource_id: str, resource_type: str):
        state = self.get_state(resource_id, resource_type)
        if state == "open":
            keys = self.get_redis_keys(resource_id, resource_type)
            opened_at = await redis_client.get(keys["opened_at"])
            if opened_at:
                time_left = self.remediation_timeout - (datetime.now().timestamp() - float(opened_at))
                return False ,"Circuit Broken. Try again in %s seconds", time_left
            return False, "Circuit Broken"
        elif state == "testing":
            #TODO: Allow limited attempts
            return False
        else:
            return True, None

    async def successful_attempt(self, resource_id, resource_type):
        keys = self.get_redis_keys(resource_id, resource_type)
        current_state = await self.get_state(resource_id, resource_type)
        success_count = await redis_client.get(keys["successes"])
        success_count = success_count + 1 if success_count else 1

        await redis_client.set(keys["successes"], str(success_count), ttl=3600)
        await redis_client.set(keys["failures"], "0", ttl=3600)

        if current_state == "testing":
            if success_count > self.max_retry_attempts:
                await self.set_state(resource_id, resource_type, "closed")
                await redis_client.set(keys["successes"], "0", ttl=3600)
        elif current_state =="closed":
            await redis_client.set(keys["failures"], "0", ttl=3600)
            await redis_client.set(keys["successes"], "0", ttl=3600)

    async def failed_attempt(self, resource_id, resource_type):
        keys = self.get_redis_keys(resource_id, resource_type)
        current_state = await self.get_state(resource_id, resource_type)
        failure_count = await redis_client.get(keys["failures"])
        failure_count = failure_count + 1 if failure_count else 1

        await redis_client.set(keys["failures"], str(failure_count), ttl=3600)
        await redis_client.set(keys["last_failure_time"], datetime.now().timestamp(), ttl=3600)
        await redis_client.set(key=["successes"], value="0", ttl=3600) #FIXME: Unlike the others

        if current_state == "testing":
            if failure_count > self.max_retry_attempts:
                await self.set_state(resource_id, resource_type, "open")
            elif current_state == "closed":
                if failure_count > self.max_retry_attempts:
                    await self.set_state(resource_id, resource_type, "open")


    async def get_status(self, resource_id: str, resource_type: str) -> dict: # Stats 4 Debugging
        keys = self.get_redis_keys(resource_id, resource_type)
        state = await self.get_state(resource_id, resource_type)

        failures = await redis_client.get(keys["failures"])
        successes = await redis_client.get(keys["successes"])
        last_failure = await redis_client.get(keys["last_failure_time"])
        opened_at = await redis_client.get(keys["opened_at"])

        return {
            "state": state,
            "consecutive_failures": int(failures) if failures else 0,
            "consecutive_successes": int(successes) if successes else 0,
            "last_failure_time": float(last_failure) if last_failure else None,
            "opened_at": float(opened_at) if opened_at else None,
            "failure_threshold": self.max_retry_attempts,
            "timeout_seconds": self.remediation_timeout,
        }

circuit_breaker = CircuitBreaker(
    max_retry_attempts= settings.max_retry_attempts,
    remediation_timeout=settings.remediation_timeout,
    health_check_interval=settings.health_check_interval
    #half_open_attempts=2,      # Need 2 successes to fully close
    #success_threshold=5,       # Reset failure count after 5 successes
)
