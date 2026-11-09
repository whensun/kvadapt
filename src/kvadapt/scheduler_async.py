from vllm.v1.core.sched.async_scheduler import AsyncScheduler

from kvadapt.scheduler_clean import KVAdaptCleanScheduler

class KVAdaptAsyncScheduler(KVAdaptCleanScheduler, AsyncScheduler):
    pass
