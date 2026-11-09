from kvadapt.scheduler_async import KVAdaptAsyncScheduler

class KVAdaptAsyncNoopScheduler(KVAdaptAsyncScheduler):
    def _maybe_reorder(self):
        return
