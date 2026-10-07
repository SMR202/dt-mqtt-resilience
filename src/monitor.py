"""Clean independent implementation of the paper's stated statistical rule."""
import statistics


def thresholds(calibration):
    return {
        'paper_3sigma': statistics.mean(calibration) + 3 * statistics.pstdev(calibration),
        'upstream_maximum': max(calibration),
    }


def flags(values, threshold):
    return [x > threshold for x in values]
