import matplotlib.pyplot as plt
import pandas as pd
import scipy.fftpack
import numpy as np

data_path = ('data/F_B_4_0.csv')
time_path = ('data/time.csv')
df1=pd.read_csv(data_path) 
df2=pd.read_csv(time_path)

# Data per column input
t0=df2['Time (seconds)']
y1=df1['Accelerometer 1 (m/s^2)']
y2=df1['Accelerometer 2 (m/s^2)']
y3=df1['Accelerometer 3 (m/s^2)']

# FFT program
# Number of samplepoints
N = 420000
# sample spacing
T = 1.0 / 84000.0

x = np.linspace(0.0, N*T, N)

yf1 = scipy.fftpack.fft(y1.values)
xf1 = np.linspace(0.0, 1.0/(2.0*T), N//2)
yf2 = scipy.fftpack.fft(y2.values)
xf2 = np.linspace(0.0, 1.0/(2.0*T), N//2)
yf3 = scipy.fftpack.fft(y3.values)
xf3 = np.linspace(0.0, 1.0/(2.0*T), N//2)

#Plotting signals
plt.figure(figsize = (12, 6))

# Signal Acc1
plt.subplot(3,1,1)
plt.plot(t0[:420000], y1[:420000], '-r', label='Acc1') 
plt.title('Signal')
# plt.xlim(0, 10)
plt.xlabel('Time')
plt.ylabel('Acc1')

# Signal Acc2
plt.subplot(3,1,2)
plt.plot(t0[:420000], y2[:420000], '-g', label='Acc2')
# plt.xlim(0, 10)
plt.xlabel('Time')
plt.ylabel('Acc2')

# Signal Acc3
plt.subplot(3,1,3)
plt.plot(t0[:420000], y3[:420000], '-b', label='Acc3')
# plt.xlim(0, 10)
plt.xlabel('Time')
plt.ylabel('Acc3')

plt.show()

# Plotting spectra

# Create a 2x2 grid of subplots
fig, ax = plt.subplots(3, 1, figsize=(10, 8))

# Top plot
ax[0].plot(xf1, 2.0 / N * np.abs(yf1[: N // 2]), color="r")
# ax[0].set_title("Plot 1")

# Middle plot
ax[1].plot(xf2, 2.0 / N * np.abs(yf2[: N // 2]), color="g")
# ax[1].set_title("Plot 2")

# Bottom plot
ax[2].plot(xf3, 2.0 / N * np.abs(yf3[: N // 2]), color="b")
# ax[2].set_title("Plot 3")

# # Bottom-right plot (Leave empty or add a 4th plot)
# ax[1, 1].axis("off")  # Hides the empty 4th subplot

plt.tight_layout()
plt.show()