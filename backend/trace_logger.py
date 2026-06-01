import json
import os
from datetime import datetime
from typing import Dict, Any

class TraceLogger:
    def __init__(self, trace_dir: str = "data/traces"):
        self.trace_dir = trace_dir
        os.makedirs(trace_dir, exist_ok=True)

    def log(self, session_id: str, step: int, harness: Dict, input_data: str, output: str, reward: float):
        trace = {
            "timestamp": datetime.now().isoformat(),
            "session": session_id,
            "step": step,
            "harness": harness,
            "input": input_data,
            "output": output,
            "reward": reward
        }
        filename = f"{session_id}_step_{step:03d}.json"
        with open(os.path.join(self.trace_dir, filename), 'w') as f:
            json.dump(trace, f, indent=2)

trace_logger = TraceLogger()
