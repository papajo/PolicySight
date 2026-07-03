"""
Lapse Bridge Scheduler
Celery background tasks for monitoring coverage windows
and automatically triggering bridge policies.
"""

import logging
from datetime import datetime, timedelta

from celery import Celery

from src.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Celery app configuration
celery_app = Celery(
    "policysight",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "check-coverage-every-hour": {
            "task": "src.core.scheduler.check_all_coverage",
            "schedule": 3600.0,  # Every hour
        },
    },
)


@celery_app.task(name="src.core.scheduler.check_all_coverage")
def check_all_coverage():
    """
    Background task that checks all registered users' coverage status.
    Runs hourly via Celery Beat.
    Triggers bridge policies for users at risk of lapse.
    """
    logger.info("Running scheduled coverage check...")
    try:
        from src.db.base import SessionLocal
        from src.db.models import User, Policy
        from src.core.lapse import CoverageGapBridge

        db = SessionLocal()
        bridge = CoverageGapBridge()

        # Get all users with active policies
        users = db.query(User).all()

        for user in users:
            active_policy = (
                db.query(Policy)
                .filter(Policy.user_id == user.id, Policy.status == "active")
                .first()
            )

            status = bridge.check_coverage_status(
                renewal_date=None,
                has_active_policy=active_policy is not None,
            )

            if bridge.should_trigger_bridge(status):
                logger.warning(
                    f"User {user.id} ({user.email}) at risk of coverage lapse. "
                    f"Alert: {bridge.generate_lapse_alert(status)}"
                )
                # In production: trigger bridge API call here
                # trigger_bridge_policy(user.id)

        db.close()
        logger.info(f"Coverage check complete. Checked {len(users)} users.")

    except Exception as e:
        logger.error(f"Coverage check failed: {e}")


@celery_app.task(name="src.core.scheduler.trigger_bridge_policy")
def trigger_bridge_policy(user_id: int):
    """
    Trigger a bridge policy for a specific user.
    This would integrate with a partner carrier API in production.
    """
    logger.info(f"Triggering bridge policy for user {user_id}...")
    from src.core.lapse import CoverageGapBridge

    bridge = CoverageGapBridge()
    cost = bridge.calculate_bridge_cost()

    # In production: call partner carrier API to issue temporary policy
    logger.info(
        f"Bridge policy for user {user_id}: "
        f"{cost['days']} days at ${cost['daily_rate']}/day = ${cost['total_cost']}"
    )

    return {
        "user_id": user_id,
        "bridge_activated": True,
        "cost": cost,
        "message": f"Bridge policy activated for {cost['days']} days.",
    }