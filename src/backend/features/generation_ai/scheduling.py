from __future__ import annotations

from typing import Any

from loguru import logger

from src.backend.features.generation_ai.services import GENERATION_AI_ARQ_TASK

RECOVERY_PAGE_SIZE = 100


async def replay_scheduling_page(task_ids: list[str], arq: Any) -> int:
    """At-least-once delivery; never remove the durable SQL intent on enqueue.

    Stable IDs deduplicate simultaneous recovery scans in ARQ. A delivered job
    still goes through the normal SQL claim, which fences duplicate execution.
    None may mean an existing job/result or an unavailable queue; retry later.
    """
    scheduled = 0
    for task_id in task_ids:
        try:
            job = await arq.enqueue_job(GENERATION_AI_ARQ_TASK, task_id, _job_id=f"generation-ai-recovery:{task_id}")
        except Exception:
            logger.bind(task_id=task_id).warning("GenerationAiSchedulingRecoveryEnqueueFailed")
            continue
        if job is not None:
            scheduled += 1
    return scheduled
