"""Eating data processor for Fresh2 Feeder with debouncing and eating detection."""

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

from ..const import _LOGGER


@dataclass
class EatingEvent:
    """Represents a single eating event."""
    start_time: datetime
    end_time: datetime
    start_weight: int  # Weight before eating (grams)
    end_weight: int    # Weight after eating (grams)
    amount: int        # Amount eaten (grams)
    duration: int      # Duration in seconds
    max_weight: int    # Maximum weight during event (detect cat stepping on bowl)


@dataclass
class WeightSample:
    """Represents a single weight measurement."""
    timestamp: datetime
    weight: int
    is_stable: bool = False


class EatingDataProcessor:
    """Processes weight data to detect eating events with debouncing."""

    def __init__(
        self,
        stable_duration_seconds: int = 60,
        sample_interval: int = 5,
        min_eating_amount: int = 2,
        spike_threshold: int = 100
    ):
        """Initialize the eating data processor.

        Args:
            stable_duration_seconds: Time with no weight change to consider stable
            sample_interval: Expected interval between samples in seconds
            min_eating_amount: Minimum weight change to consider as eating (grams)
            spike_threshold: Weight increase threshold to detect cat stepping on bowl
        """
        self.stable_duration_seconds = stable_duration_seconds
        self.sample_interval = sample_interval
        self.min_eating_amount = min_eating_amount
        self.spike_threshold = spike_threshold

        # Data storage
        self.weight_samples = deque(maxlen=720)  # 1 hour of data at 5s intervals
        self.last_stable_weight = None
        self.last_stable_time = None
        self.stability_start_time = None
        self.stability_weight = None

    def add_sample(self, weight: int, timestamp: datetime) -> WeightSample:
        """Add a weight sample to the history.

        Args:
            weight: Weight in grams
            timestamp: Sample timestamp

        Returns:
            WeightSample with stability status
        """
        sample = WeightSample(timestamp=timestamp, weight=weight)

        # Check if this sample represents stable weight
        is_stable, stable_weight = self.check_stability()
        if is_stable:
            sample.is_stable = True
            if stable_weight != self.last_stable_weight:
                self.last_stable_weight = stable_weight
                self.last_stable_time = timestamp
                _LOGGER.debug(f"New stable weight detected: {stable_weight}g at {timestamp}")

        self.weight_samples.append(sample)
        return sample

    def check_stability(self) -> Tuple[bool, int]:
        """Check if weight has been stable for the required duration.

        Returns:
            Tuple of (is_stable, stable_weight)
        """
        if len(self.weight_samples) < 2:
            return False, 0

        current_time = self.weight_samples[-1].timestamp
        current_weight = self.weight_samples[-1].weight

        # Check samples from the last stable_duration_seconds
        cutoff_time = current_time - timedelta(seconds=self.stable_duration_seconds)
        recent_samples = [s for s in self.weight_samples if s.timestamp > cutoff_time]

        if not recent_samples:
            return False, 0

        # Get all weights in this period
        weights = [s.weight for s in recent_samples]

        # For integer weights, stability means all values are identical
        if len(set(weights)) == 1:
            # Verify sufficient time span
            time_span = (recent_samples[-1].timestamp - recent_samples[0].timestamp).total_seconds()
            if time_span >= self.stable_duration_seconds - self.sample_interval:
                return True, weights[0]

        return False, 0

    def detect_spike(self, weight: int) -> bool:
        """Detect if weight spike indicates cat stepping on bowl.

        Args:
            weight: Current weight

        Returns:
            True if spike detected
        """
        if not self.last_stable_weight:
            return False

        # Check if weight increased dramatically from stable
        if weight > self.last_stable_weight + self.spike_threshold:
            _LOGGER.debug(f"Weight spike detected: {self.last_stable_weight}g -> {weight}g")
            return True

        return False

    def get_recent_samples(self, seconds: int) -> List[WeightSample]:
        """Get samples from the last N seconds.

        Args:
            seconds: Number of seconds to look back

        Returns:
            List of recent samples
        """
        if not self.weight_samples:
            return []

        cutoff_time = self.weight_samples[-1].timestamp - timedelta(seconds=seconds)
        return [s for s in self.weight_samples if s.timestamp > cutoff_time]

    def calculate_weight_change_rate(self, window_seconds: int = 60) -> float:
        """Calculate rate of weight change in grams per minute.

        Args:
            window_seconds: Time window for calculation

        Returns:
            Rate of change in grams per minute
        """
        recent_samples = self.get_recent_samples(window_seconds)
        if len(recent_samples) < 2:
            return 0.0

        first_weight = recent_samples[0].weight
        last_weight = recent_samples[-1].weight
        time_diff = (recent_samples[-1].timestamp - recent_samples[0].timestamp).total_seconds()

        if time_diff == 0:
            return 0.0

        # Convert to grams per minute
        return abs(last_weight - first_weight) * 60 / time_diff


class EatingStateMachine:
    """State machine for detecting eating events."""

    def __init__(
        self,
        processor: EatingDataProcessor,
        min_eating_amount: int = 2
    ):
        """Initialize the state machine.

        Args:
            processor: EatingDataProcessor instance
            min_eating_amount: Minimum amount to consider as eating
        """
        self.processor = processor
        self.min_eating_amount = min_eating_amount

        # State tracking
        self.state = "IDLE"  # IDLE, EATING, STABILIZING
        self.eating_start_time = None
        self.eating_start_weight = None
        self.max_weight_during_eating = None
        self.stability_check_start = None
        self.stability_check_weight = None
        self.last_event = None

    def process_weight(self, weight: int, timestamp: datetime) -> Optional[EatingEvent]:
        """Process a weight update and detect eating events.

        Args:
            weight: Current weight in grams
            timestamp: Current timestamp

        Returns:
            EatingEvent if an eating session completed, None otherwise
        """
        # Add sample to processor
        sample = self.processor.add_sample(weight, timestamp)

        # Update max weight tracking
        if self.state == "EATING" and self.max_weight_during_eating is not None:
            self.max_weight_during_eating = max(self.max_weight_during_eating, weight)

        # State machine logic
        if self.state == "IDLE":
            return self._handle_idle_state(weight, timestamp, sample)
        elif self.state == "EATING":
            return self._handle_eating_state(weight, timestamp, sample)
        elif self.state == "STABILIZING":
            return self._handle_stabilizing_state(weight, timestamp, sample)

        return None

    def _handle_idle_state(
        self,
        weight: int,
        timestamp: datetime,
        sample: WeightSample
    ) -> Optional[EatingEvent]:
        """Handle IDLE state transitions."""
        # Need stable weight to detect eating start
        if not self.processor.last_stable_weight:
            return None

        # Check if eating started (weight decreased from stable)
        if weight < self.processor.last_stable_weight - self.min_eating_amount:
            self.state = "EATING"
            self.eating_start_time = timestamp
            self.eating_start_weight = self.processor.last_stable_weight
            self.max_weight_during_eating = weight
            _LOGGER.info(
                f"Eating started: {self.eating_start_weight}g -> {weight}g at {timestamp}"
            )

        return None

    def _handle_eating_state(
        self,
        weight: int,
        timestamp: datetime,
        sample: WeightSample
    ) -> Optional[EatingEvent]:
        """Handle EATING state transitions."""
        # Check if weight has stabilized
        if not self.stability_check_start or weight != self.stability_check_weight:
            # Weight changed or first stability check
            self.stability_check_start = timestamp
            self.stability_check_weight = weight
            return None

        # Weight unchanged, check duration
        stability_duration = (timestamp - self.stability_check_start).total_seconds()

        if stability_duration >= 10:  # 10 seconds of no change to enter stabilizing
            self.state = "STABILIZING"
            _LOGGER.debug(f"Entering stabilizing state at {weight}g")

        return None

    def _handle_stabilizing_state(
        self,
        weight: int,
        timestamp: datetime,
        sample: WeightSample
    ) -> Optional[EatingEvent]:
        """Handle STABILIZING state transitions."""
        # Check if weight changed (eating resumed)
        if weight != self.stability_check_weight:
            # Back to eating
            self.state = "EATING"
            self.stability_check_start = timestamp
            self.stability_check_weight = weight
            _LOGGER.debug(f"Eating resumed: weight changed to {weight}g")
            return None

        # Check if stable long enough to end eating
        stability_duration = (timestamp - self.stability_check_start).total_seconds()

        if stability_duration >= self.processor.stable_duration_seconds:
            # Eating ended
            event = self._create_eating_event(timestamp, weight)

            # Reset state
            self.state = "IDLE"
            self.eating_start_time = None
            self.eating_start_weight = None
            self.stability_check_start = None
            self.stability_check_weight = None
            self.max_weight_during_eating = None
            self.last_event = event

            _LOGGER.info(
                f"Eating ended: {event.amount}g consumed in {event.duration}s"
            )

            return event

        return None

    def _create_eating_event(self, end_time: datetime, end_weight: int) -> EatingEvent:
        """Create an eating event from current state."""
        amount = max(0, self.eating_start_weight - end_weight)
        duration = int((end_time - self.eating_start_time).total_seconds())

        return EatingEvent(
            start_time=self.eating_start_time,
            end_time=end_time,
            start_weight=self.eating_start_weight,
            end_weight=end_weight,
            amount=amount,
            duration=duration,
            max_weight=self.max_weight_during_eating or end_weight
        )

    @property
    def is_eating(self) -> bool:
        """Check if currently eating."""
        return self.state in ("EATING", "STABILIZING")

    @property
    def current_eating_amount(self) -> int:
        """Get current eating amount if eating."""
        if not self.is_eating or not self.eating_start_weight:
            return 0

        current_weight = self.stability_check_weight or 0
        return max(0, self.eating_start_weight - current_weight)

    @property
    def current_eating_duration(self) -> int:
        """Get current eating duration in seconds."""
        if not self.is_eating or not self.eating_start_time:
            return 0

        return int((datetime.now() - self.eating_start_time).total_seconds())