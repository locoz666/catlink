"""Models for additional device configuration."""

from pydantic import BaseModel


class AdditionalDeviceConfig(BaseModel):
    """Additional device configuration."""

    name: str = ""
    mac: str = ""
    empty_weight: float = 0.0
    max_samples_litter: int = 24

    # Eating detection parameters for Fresh2 Feeder
    stable_duration: int = 60  # Time with no weight change to consider stable (seconds)
    min_eating_amount: int = 2  # Minimum weight change to consider as eating (grams)
    spike_threshold: int = 100  # Weight increase threshold to detect cat stepping on bowl (grams)
