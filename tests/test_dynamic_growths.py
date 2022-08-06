import random

"""
With 50% growth, 38 level-ups
random level-up variance of 2.5 stats off average
dynamic level-up variance of 0.8 stats off average
With 30% growth, 38 level-ups
random level-up variance of 2.3 stats off average
dynamic level-up variance of 0.7 stats off average
With 10% growth, 38 level-ups
random level-up variance of 1.6 stats off average
dyanmic level-up variance of 0.5 stats off average
With 90% growth, 38 level-ups
random level-up variance of 2.25 stats off average
dynamic level-up variane of 0.7 stats off average

"""

growth = 25
constant = 10.
num_trials = 1000
dynamic_variance = 0
random_variance = 0
ddirectionality = 0
rdirectionality = 0

for _ in range(num_trials):
    num_levels = 19
    avg_stat = num_levels * (growth / 100.)
    growth_points = 0
    dynamic_stat = 0
    for num in range(num_levels):
        start_growth = growth + growth_points
        if num_trials == 1:
            print(start_growth)
        if start_growth <= 0:
            growth_points += growth/5.
        else:
            num_tries = growth // 100
            free_levels = num_tries
            dynamic_stat += free_levels
            new_growth = growth % 100
            start_growth = new_growth + growth_points
            val = random.randint(0, 99)
            if num_trials == 1:
                print("Roll: %d" % val)
            if val < int(start_growth):
                dynamic_stat += 1
                growth_points -= (100 - new_growth)/constant
            else:
                growth_points += new_growth/constant

    random_stat = 0
    for num in range(num_levels):
        start_growth = growth
        while start_growth > 0:
            val = random.randint(0, 99)
            if val < int(start_growth):
                random_stat += 1
            start_growth -= 100

    if num_trials == 1:
        print("Average Stat: %f" % avg_stat)
        print("Dynamic Stat: %f" % dynamic_stat)
        print("Random Stat: %f" % random_stat)
    dynamic_variance += abs(dynamic_stat - avg_stat)
    ddirectionality += dynamic_stat - avg_stat
    random_variance += abs(random_stat - avg_stat)
    rdirectionality += random_stat - avg_stat

    if abs(dynamic_stat - avg_stat) > 5:
        print(dynamic_stat, avg_stat)

print("Dynamic Variance: %f" % (dynamic_variance/num_trials))
print("Random Variance: %f" % (random_variance/num_trials))
print("Dynamic Directionality: %f" % (ddirectionality/num_trials))
print("Random Directionality: %f" % (rdirectionality/num_trials))
