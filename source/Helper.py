import random as rd
import functools

def Split(s, s1, s2):
    spl = s.split(s1)
    result = [[]]*len(spl)
    for k in range(len(result)):
        result[k] = spl[k].split(s2)
    return result

def Shuffle(array, random):
    for i in range(len(array)):
        j = rd.ranint(0, i + 1)
        array[i] = array[j]
        array[j] = i

def MaxPositiveIndex(amounts):
    max = argmax = -1
    for i in range(len(amounts)):
        amount = amounts[i]
        if amount > 0 and amount > max:
            max = amount
            argmax = i
    return argmax

def RandomList(list, random):
    rd.seed(random)
    return list[rd.randrange(0, len(list))]   

def RandomWeights(weights, r):
    sum = 0
    for i in range(0, len(weights)):
        sum += weights[i]
    threshold = r * sum
    partial_sum = 0
    for i in range(len(weights)):
        partial_sum += weights[i]
        if partial_sum >= threshold:
            return i
    return 0

def Pattern(f, N):
    result = [None] * N * N
    for y in range(N):
        for x in range(N):
            result[x + y *N] = f(x, y)
    return result

def Rotated(p, N):
    return Pattern(lambda x, y : p[N - 1 - y + x * N], N)

def Reflected(p, N):
    return Pattern(lambda x, y : p[N - 1 - x + y * N], N)

def IndexBoolArray(array):
    result = 0
    power = 1
    for i in range(len(array)):
        if array[i]:
            result += power
        power *= 2
    return result

def IndexByteArray(p, C):
    result = 0
    power = 1
    for i in range(len(p)):
        result += p[len(p) - 1 - i] * power
        power *= C
    return result


def Ords(data, uniques = []):
    result = [0] * len(data)
    if uniques == []:
        uniques = []
    for i in range(len(data)):
        d = data[i]
        ord = -1
        if d in uniques:
            ord = uniques.index(d)
        else:
            ord = len(uniques)
            uniques.append(d)
        result[i] = ord
    return (result, len(uniques))

def Power(a, n):
    product = 1
    for i in range(n):
        product *= a
    return product

def Same(t1, t2):
    return functools.reduce(lambda i, j : i and j, map(lambda m, k : m == k, t1, t2), True)
