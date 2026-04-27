from decimal import Decimal


def percent_change(start_price: Decimal | None, end_price: Decimal | None) -> Decimal | None:
    if start_price is None or end_price is None or start_price == Decimal("0"):
        return None
    return ((end_price - start_price) / start_price * Decimal("100")).quantize(Decimal("0.00001"))


def direction_from_percent_change(value: Decimal | None) -> str | None:
    if value is None:
        return None
    if value > Decimal("0.10"):
        return "up"
    if value < Decimal("-0.10"):
        return "down"
    return "flat"


def direction_correct(predicted_direction: str | None, actual_direction: str | None) -> bool | None:
    if predicted_direction is None or actual_direction is None or predicted_direction == "uncertain":
        return None
    return predicted_direction == actual_direction


def absolute_error(predicted: Decimal | None, actual: Decimal | None) -> Decimal | None:
    if predicted is None or actual is None:
        return None
    return abs(predicted - actual).quantize(Decimal("0.00001"))
