import asyncio
import logging
from typing import Dict, List, Optional, Callable, Awaitable
from enum import Enum

logger = logging.getLogger(__name__)


class QueueState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


class JobStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"


class QueueManager:
    def __init__(self):
        self.state: QueueState = QueueState.IDLE
        self.jobs: Dict[str, dict] = {}  # job_id -> job_data
        self.queue: List[str] = []       # ordered list of job_ids
        self._task: Optional[asyncio.Task] = None
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # not paused by default
        self._process_fn: Optional[Callable] = None

    def set_processor(self, fn: Callable):
        """Set the async function that processes each job."""
        self._process_fn = fn

    def add_job(self, job_id: str, data: dict):
        """Add a job to the queue."""
        self.jobs[job_id] = {**data, "status": JobStatus.PENDING}
        self.queue.append(job_id)
        logger.info(f"Job {job_id} added to queue")

    def get_status(self) -> dict:
        return {
            "state": self.state,
            "total": len(self.jobs),
            "pending": sum(1 for j in self.jobs.values() if j["status"] == JobStatus.PENDING),
            "analyzing": sum(1 for j in self.jobs.values() if j["status"] == JobStatus.ANALYZING),
            "done": sum(1 for j in self.jobs.values() if j["status"] == JobStatus.DONE),
            "error": sum(1 for j in self.jobs.values() if j["status"] == JobStatus.ERROR),
        }

    def update_job(self, job_id: str, **kwargs):
        if job_id in self.jobs:
            self.jobs[job_id].update(kwargs)

    async def start(self):
        """Start or resume processing the queue."""
        if self.state == QueueState.RUNNING:
            return
        if self.state == QueueState.PAUSED:
            self._pause_event.set()
            self.state = QueueState.RUNNING
            logger.info("Queue resumed")
            return

        self.state = QueueState.RUNNING
        self._pause_event.set()
        self._task = asyncio.create_task(self._run())
        logger.info("Queue started")

    async def pause(self):
        """Pause after current job finishes."""
        if self.state == QueueState.RUNNING:
            self._pause_event.clear()
            self.state = QueueState.PAUSED
            logger.info("Queue paused")

    async def stop(self):
        """Stop queue. Keep completed results, cancel pending."""
        self.state = QueueState.STOPPED
        self._pause_event.set()  # unblock if paused

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        # Mark all pending jobs as cancelled
        for job_id in self.queue:
            job = self.jobs.get(job_id, {})
            if job.get("status") == JobStatus.PENDING:
                self.jobs[job_id]["status"] = JobStatus.CANCELLED

        self.state = QueueState.IDLE
        logger.info("Queue stopped")

    async def reset(self):
        """Clear everything."""
        await self.stop()
        self.jobs.clear()
        self.queue.clear()
        self.state = QueueState.IDLE

    async def _run(self):
        """Main processing loop."""
        try:
            for job_id in list(self.queue):
                # Check if stopped
                if self.state == QueueState.STOPPED:
                    break

                job = self.jobs.get(job_id)
                if not job or job["status"] != JobStatus.PENDING:
                    continue

                # Wait if paused
                await self._pause_event.wait()

                if self.state == QueueState.STOPPED:
                    break

                # Process the job
                self.jobs[job_id]["status"] = JobStatus.ANALYZING
                logger.info(f"Processing job {job_id}")

                try:
                    if self._process_fn:
                        result = await self._process_fn(job_id, job)
                        self.jobs[job_id].update({
                            "status": JobStatus.DONE,
                            **result
                        })
                        logger.info(f"Job {job_id} completed")
                except asyncio.CancelledError:
                    self.jobs[job_id]["status"] = JobStatus.CANCELLED
                    raise
                except Exception as e:
                    logger.error(f"Job {job_id} failed: {e}")
                    self.jobs[job_id]["status"] = JobStatus.ERROR
                    self.jobs[job_id]["error"] = str(e)

        except asyncio.CancelledError:
            logger.info("Queue task cancelled")
        finally:
            if self.state != QueueState.STOPPED:
                self.state = QueueState.IDLE
            logger.info("Queue processing finished")


# Global queue instance
queue_manager = QueueManager()
