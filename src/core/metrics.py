from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time


# Health Check Metrics
health_checks_total = Counter(
    "health_checks_total",
    "Total number of health checks performed",
    ["resource_type", "status"],
)

health_check_duration_seconds = Histogram(
    "health_check_duration_seconds",
    "Duration of health checks in seconds",
    ["resource_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)

# Incident Metrics
incidents_total = Counter(
    "incidents_total",
    "Total number of incidents created",
    ["resource_type", "severity", "status"],
)

incidents_open = Gauge(
    "incidents_open",
    "Number of currently open incidents",
    ["resource_type", "severity"],
)

# Remediation Metrics
remediations_total = Counter(
    "remediations_total",
    "Total number of remediations attempted",
    ["resource_type", "action", "status"],
)

remediation_duration_seconds = Histogram(
    "remediation_duration_seconds",
    "Duration of remediation actions in seconds",
    ["resource_type", "action"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)

auto_remediations_total = Counter(
    "auto_remediations_total",
    "Total number of automatically executed remediations",
    ["resource_type", "action"],
)

manual_approvals_total = Counter(
    "manual_approvals_total",
    "Total number of remediations requiring manual approval",
    ["resource_type", "action", "approved"],
)

# Resource Metrics
monitored_resources = Gauge(
    "monitored_resources",
    "Number of resources currently monitored",
    ["resource_type", "status"],
)

# API Metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0],
)

# Worker Metrics
worker_loop_duration_seconds = Histogram(
    "worker_loop_duration_seconds",
    "Duration of worker loop iterations in seconds",
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0],
)

worker_errors_total = Counter(
    "worker_errors_total", "Total number of worker errors", ["error_type"]
)


# Decorator for timing functions
def track_duration(metric: Histogram, labels: dict = None):
    """
    Decorator to track function execution duration

    Usage:
        @track_duration(health_check_duration_seconds, {'resource_type': 'ec2'})
        async def check_health(self, instance_id):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        return wrapper

    return decorator


# Helper functions for common metric patterns
class MetricsHelper:
    """Helper methods for recording metrics"""

    @staticmethod
    def record_health_check(resource_type: str, status: str, duration: float):
        """Record a health check completion"""
        health_checks_total.labels(resource_type=resource_type, status=status).inc()

        health_check_duration_seconds.labels(resource_type=resource_type).observe(
            duration
        )

    @staticmethod
    def record_incident(resource_type: str, severity: str, status: str = "open"):
        """Record an incident creation"""
        incidents_total.labels(
            resource_type=resource_type, severity=severity, status=status
        ).inc()

    @staticmethod
    def record_remediation(
        resource_type: str,
        action: str,
        status: str,
        duration: float,
        auto_executed: bool = False,
    ):
        """Record a remediation attempt"""
        remediations_total.labels(
            resource_type=resource_type, action=action, status=status
        ).inc()

        remediation_duration_seconds.labels(
            resource_type=resource_type, action=action
        ).observe(duration)

        if auto_executed:
            auto_remediations_total.labels(
                resource_type=resource_type, action=action
            ).inc()

    @staticmethod
    def update_open_incidents_gauge(resource_type: str, severity: str, count: int):
        """Update the gauge for open incidents"""
        incidents_open.labels(resource_type=resource_type, severity=severity).set(count)

    @staticmethod
    def update_monitored_resources_gauge(resource_type: str, status: str, count: int):
        """Update the gauge for monitored resources"""
        monitored_resources.labels(resource_type=resource_type, status=status).set(
            count
        )


def get_metrics():
    """Return Prometheus metrics in text format"""
    return generate_latest()


def get_metrics_content_type():
    """Return the content type for Prometheus metrics"""
    return CONTENT_TYPE_LATEST
