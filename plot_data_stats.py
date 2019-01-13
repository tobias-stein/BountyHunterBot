import pickle
import matplotlib.pyplot as plt
import os

from tqdm import tqdm
from constants import *


acc_rewards = []

for filename in tqdm([os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR)], desc="Read training samples"):
    with open(filename, "rb") as f:
        data = pickle.load(f)

        acc_rwd = 0
        for d in data:
            acc_rwd += d[8]

        acc_rewards.append(acc_rwd)

# the histogram of the data
plt.hist(acc_rewards, 15, normed=1, facecolor='green', alpha=0.75)
plt.title(f"Avg. Reward: {sum(acc_rewards)/len(acc_rewards)}")
plt.show()