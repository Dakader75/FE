offense = [i/100. for i in range(0, 100, 5)]
defense = [i/100. for i in range(0, 100, 5)]

offense_bias = 2
offense_weight = offense_bias * (1 / (offense_bias + 1))
defense_weight = 1 - offense_weight
print(offense_weight, defense_weight)

def utility(offe, defe):
    if offe <= 0:
        return 0
    return (offe * offense_weight) + (defe * defense_weight)

for o in offense:
    for d in defense:
        print('%.2f' % utility(o, d))