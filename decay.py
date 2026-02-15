import math

def exponential_decay_factor(
    current_time: float,
    last_seen: float,
    half_life_hours: float
) -> float:
    if half_life_hours <= 0:
        return 1.0
    hours = (current_time - last_seen) / 3600.0
    if hours <= 0:
        return 1.0
    rate = 0.693 / half_life_hours
    return math.exp(-rate * hours)