import numpy as np
import matplotlib.pyplot as plt
count = np.load('C:/Users/USER/sw/sw_2/total_char.npy') # 이 부분 경로 수정
plt.figure(figsize=(15,10))
plt.xlabel("5 sec bins")
plt.ylabel("# of characters")
plt.bar(np.arange(len(count)),count,width=1)
plt.show()