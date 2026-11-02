from tenacity import retry, stop_after_attempt, wait_fixed

retry_on_failure = retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(0.1),
    reraise=True,
)
