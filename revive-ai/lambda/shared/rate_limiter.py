"""Token bucket rate limiter for API calls."""
import time
import threading


class TokenBucketRateLimiter:
    """Thread-safe token bucket rate limiter."""

    def __init__(self, rate_per_minute: int, burst: int = None):
        """
        Initialize rate limiter.

        Args:
            rate_per_minute: Maximum requests per minute
            burst: Maximum burst capacity (defaults to rate_per_minute)
        """
        self.rate = rate_per_minute
        self.burst = burst or rate_per_minute
        self.tokens = float(self.burst)
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens. Blocks until tokens are available.

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Returns:
            True when tokens are acquired
        """
        while True:
            with self.lock:
                now = time.time()
                elapsed = now - self.last_refill

                # Refill tokens based on elapsed time
                new_tokens = elapsed * (self.rate / 60.0)  # Convert per-minute to per-second
                self.tokens = min(self.burst, self.tokens + new_tokens)
                self.last_refill = now

                # Check if we have enough tokens
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

            # Wait a bit before retrying
            time.sleep(0.1)

    def get_available_tokens(self) -> float:
        """Get current number of available tokens."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            new_tokens = elapsed * (self.rate / 60.0)
            return min(self.burst, self.tokens + new_tokens)
