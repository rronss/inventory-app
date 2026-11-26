from app.alerts import send_low_stock_alert


def test_low_stock_alert_is_sent():
    outbox = []
    sent = send_low_stock_alert("KB-02", outbox)
    assert sent.wait(timeout=0.25), "alert not sent within 0.25s"
    assert outbox == ["KB-02 is running low"]
