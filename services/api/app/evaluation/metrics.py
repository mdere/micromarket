def direction_correct(predicted: str, actual: str) -> bool:
    return predicted == actual


def absolute_error(predicted_percent: float, actual_percent: float) -> float:
    return abs(predicted_percent - actual_percent)
