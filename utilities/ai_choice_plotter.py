import numpy as np
import matplotlib.pyplot as plt

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

arr = np.zeros((len(offense), len(defense)))
for cidx, o in enumerate(offense):
    for ridx, d in enumerate(defense):
        arr[ridx][cidx] = utility(o, d)

plt.imshow(arr)
plt.show()