from itertools import islice

from vllm.v1.core.sched.interface import PauseState
from vllm.v1.core.sched.request_queue import FCFSRequestQueue
from vllm.v1.core.sched.scheduler import Scheduler
from vllm.v1.request import RequestStatus

from kvadapt.admission_bypass import choose_bypass_index

class KVAdaptCleanScheduler(Scheduler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bypass_counts = {}

    def _maybe_reorder(self):
        if not isinstance(self.waiting, FCFSRequestQueue):
            return

        if not self.scheduler_reserve_full_isl:
            return

        if self._pause_state != PauseState.UNPAUSED:
            return

        if self.kv_holding_waiting:
            return

        if self.connector is not None or self.ec_connector is not None:
            return

        if self.vllm_config.speculative_config is not None:
            return

        if len(self.running) + self.num_waiting_for_streaming_input >= self.max_num_active_reqs:
            return

        requests = list(islice(self.waiting, 4))

        if len(requests) < 2:
            return

        if any(
            request.status != RequestStatus.WAITING
            or request.num_computed_tokens != 0
            or request.has_encoder_inputs
            for request in requests
        ):
            return

        free_blocks = self.kv_cache_manager.block_pool.get_num_free_blocks()
        watermark_blocks = self.kv_cache_manager.watermark_blocks if self.running else 0
        available_blocks = max(0, free_blocks - watermark_blocks)

        required_blocks = [
            (min(request.num_tokens, self.max_model_len) + self.block_size - 1)
            // self.block_size
            for request in requests
        ]

        head = requests[0]
        bypass_count = self.bypass_counts.get(head.request_id, 0)

        index = choose_bypass_index(
            required_blocks,
            available_blocks,
            bypass_count=bypass_count,
            max_bypasses=getattr(self, 'max_bypasses', 2),
        )

        if index is None:
            return

        selected = requests[index]

        self.waiting.remove_request(selected)
        self.waiting.prepend_request(selected)

        self.bypass_counts[head.request_id] = bypass_count + 1

        if len(self.bypass_counts) > 256:
            waiting_ids = {request.request_id for request in self.waiting}
            self.bypass_counts = {
                request_id: count
                for request_id, count in self.bypass_counts.items()
                if request_id in waiting_ids
            }

    def schedule(self, throttle_prefills: bool = False):
        self._maybe_reorder()
        return super().schedule(throttle_prefills=throttle_prefills)
