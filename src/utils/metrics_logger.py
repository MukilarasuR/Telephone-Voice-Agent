import csv
import os
import datetime
import logging
import atexit
import sys

# Store metrics in memory until exit
_metrics = []

def log_duration(label: str, start: float, end: float):
    duration = round(end - start, 3)
    timestamp = datetime.datetime.now().isoformat()
    _metrics.append((timestamp, label, duration))
    logging.info(f"[Timing] {label}: {duration:.3f}s")

def save_metrics_on_exit():
    try:
        if not _metrics:
            logging.warning("No metrics collected - nothing to save")
            return

        # Create metrics directory if it doesn't exist
        metrics_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "metrics")
        os.makedirs(metrics_dir, exist_ok=True)
        
        filename = f"response_metrics_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(metrics_dir, filename)
        
        logging.info(f"Attempting to save metrics to: {filepath}")
        
        with open(filepath, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "component", "duration_seconds"])
            writer.writerows(_metrics)

        print(f"\n✅ Metrics saved to: {filepath}")
        logging.info(f"Successfully saved {len(_metrics)} metrics to {filepath}")
        return filepath  # Return path for verification
    except Exception as e:
        logging.error(f"Failed to save metrics: {str(e)}", exc_info=True)
        print(f"\n❌ Failed to save metrics: {str(e)}")

# Register exit handler
atexit.register(save_metrics_on_exit)

# Also register handler for SIGTERM/SIGINT
if sys.platform != "win32":
    import signal
    signal.signal(signal.SIGTERM, lambda *_: save_metrics_on_exit())
    signal.signal(signal.SIGINT, lambda *_: save_metrics_on_exit())
