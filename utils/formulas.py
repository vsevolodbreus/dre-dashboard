def percent_change(x1: float, x2: float) -> float:
    """Calulates the percent change from x1 -> x2"""
    if x1 == 0:
        return 0

    return (x2 - x1) / x1 * 100
