import math

num_levels = 19
growth_rate = 30

n = num_levels
p = growth_rate / 100
# x = expected_stat_ups

x = n*p
print("Expected Stat Ups: %.3f" % x)

def fact(n, k):
    return math.factorial(n) / math.factorial(k) / math.factorial(n - k)

def binom(x, n, p):
    if x > n:
        return 0
    return fact(n, x) * p**x * (1-p)**(n-x)

def cdf(j, n, p):
    total = 0
    for i in range(0, j + 1):
        total += binom(i, n, p)
    return total

def cdf2(x, n1, p1, n2, p2):
    total = 0
    for j in range(x + 1):
        for i in range(j + 1):
            a = binom(i, n1, p1)
            b = binom(j - i, n2, p2)
            total += (a * b)
    return total

def quantile(q, n, p):
    for x in range(n + 1):
        prob = cdf(x, n, p)
        if prob > q:
            return x
    return n

def quantile2(q, n1, p1, n2, p2):
    for x in range(n1 + n2 + 1):
        prob = cdf2(x, n1, p1, n2, p2)
        if prob > q:
            return x
    return n

x = 3
assert x <= n
# print("Probability of %d stat ups: %.3f %%" % (x, binom(x, n, p)*100))
# print("Probability of <=%d stat ups: %.3f %%" % (x, cdf(x, n, p)*100))
# print("Num stat ups at 10%% quantile: %d" % (quantile(.1, n, p)))
# print("Num stat ups at 50%% quantile: %d" % (quantile(.5, n, p)))
# print("Num stat ups at 90%% quantile: %d" % (quantile(.9, n, p)))

n1 = 19; p1 = .2; n2 = 9; p2 = .25
x = 5
# print("Probability of %d stat ups: %.3f %%" % (x, binom(x, n, p)*100))
# print("Probability of <=%d stat ups: %.3f %%" % (x, cdf(x, n1, p1)*100))
print("Probability of <=%d stat ups: %.3f %%" % (x, cdf2(x, n1, p1, n2, p2)*100))
print("Num stat ups at 10%% quantile: %d" % (quantile2(.1, n1, p1, n2, p2)))
print("Num stat ups at 50%% quantile: %d" % (quantile2(.5, n1, p1, n2, p2)))
print("Num stat ups at 90%% quantile: %d" % (quantile2(.9, n1, p1, n2, p2)))
