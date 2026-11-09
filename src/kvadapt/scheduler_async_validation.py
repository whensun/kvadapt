import json
import os
from pathlib import Path

from kvadapt.scheduler_async_one_bypass import KVAdaptAsyncOneBypassScheduler

class KVAdaptAsyncValidationScheduler(KVAdaptAsyncOneBypassScheduler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kvadapt_path = Path(os.environ['KVADAPT_VALIDATION_PATH'])
        self.kvadapt_path.parent.mkdir(parents=True, exist_ok=True)
        self.kvadapt_selected = None
        self.kvadapt_stats = {
            'schedule_calls': 0,
            'reorders': 0,
            'scheduled_after_reorder': 0,
            'not_scheduled_after_reorder': 0,
            'max_observed_bypass_count': 0,
        }
        self._save_validation()

    def _save_validation(self):
        self.kvadapt_path.write_text(json.dumps(self.kvadapt_stats, indent=2))

    def _maybe_reorder(self):
        before = next(iter(self.waiting), None)
        super()._maybe_reorder()
        after = next(iter(self.waiting), None)

        if before is None or after is None:
            return

        if before.request_id == after.request_id:
            return

        bypass_count = self.bypass_counts.get(before.request_id, 0)

        if bypass_count != 1:
            raise AssertionError(f'Unexpected bypass count: {bypass_count}')

        self.kvadapt_selected = after.request_id
        self.kvadapt_stats['reorders'] += 1
        self.kvadapt_stats['max_observed_bypass_count'] = max(
            self.kvadapt_stats['max_observed_bypass_count'],
            bypass_count,
        )

    def schedule(self, throttle_prefills=False):
        self.kvadapt_selected = None
        output = super().schedule(throttle_prefills=throttle_prefills)
        self.kvadapt_stats['schedule_calls'] += 1

        if self.kvadapt_selected is not None:
            if self.kvadapt_selected in output.num_scheduled_tokens:
                self.kvadapt_stats['scheduled_after_reorder'] += 1
            else:
                self.kvadapt_stats['not_scheduled_after_reorder'] += 1

            self._save_validation()

        return output
