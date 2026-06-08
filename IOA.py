from numpy import ndarray, power, abs
#IOA: index of assessment


def calculate_IOA(data1: ndarray, data2: ndarray):
    factor = power(data1-data2, 2).sum()
    mean = data1.mean()
    denominator = power(abs(data1-mean) + abs(data2-mean), 2).sum()

    return round(1 - factor/denominator, 2)