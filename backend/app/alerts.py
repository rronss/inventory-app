import random
import threading
import time


def send_low_stock_alert(sku: str, outbox: list[str]) -> threading.Event:
    """Send the alert in the background. The returned event is set once the mail gateway has accepted it."""
    sent = threading.Event()

    def deliver():
        time.sleep(random.uniform(0.15, 0.5))  # the mail gateway takes a moment to answer
        outbox.append(f"{sku} is running low")
        sent.set()

    threading.Thread(target=deliver, daemon=True).start()
    return sent
