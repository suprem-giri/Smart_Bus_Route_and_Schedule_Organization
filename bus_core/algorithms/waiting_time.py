"""
Algorithm 4: Waiting-Time Estimation.
Calculates estimated passenger waiting time based on scheduled headway (service interval).
"""


def estimate_waiting_time(service_interval):
    """
    Estimates the average passenger waiting time assuming random arrivals
    over a uniform service interval H.

    Formula: W_avg = H / 2
    
    Args:
        service_interval (float or int): Service headway in minutes.
        
    Returns:
        float: Estimated average waiting time in minutes.
        
    Raises:
        ValueError: If service_interval <= 0.
    """
    if service_interval is None or service_interval <= 0:
        raise ValueError("Invalid service interval: Must be greater than 0.")
    return round(float(service_interval) / 2.0, 2)


def estimate_waiting_time_safe(service_interval, default=0.0):
    """Safe wrapper returning default if interval is invalid."""
    try:
        return estimate_waiting_time(service_interval)
    except (ValueError, TypeError):
        return default
