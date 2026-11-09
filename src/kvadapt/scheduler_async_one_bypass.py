from kvadapt.scheduler_async import KVAdaptAsyncScheduler

class KVAdaptAsyncOneBypassScheduler(KVAdaptAsyncScheduler):
    max_bypasses = 1
