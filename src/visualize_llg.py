# src/visualize_llg_3d.py
import os
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Load a single step
df = pd.read_csv("edp/data_llg/step_50.csv", header=None, delim_whitespace=True)

# Extract data
x, y, z = df[0], df[1], df[2]  # z is all 0
u, v, w = df[3], df[4], df[5]

# Create 3D figure
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Plot the unit disk (green mesh)
ax.plot_trisurf(x, y, z, color='lightgreen', alpha=0.3, linewidth=0.2, edgecolor='green')

# Plot quiver vectors
ARROW_LENGTH_RATIO=0.4
ax.quiver(x, y, z, u, v, w, length=ARROW_LENGTH_RATIO, normalize=True, color='blue')

# Tidy up
ax.set_xlim([-1, 1])
ax.set_ylim([-1, 1])
ax.set_zlim([-1, 1])
ax.set_title("Magnetization vector field at step 50")

# Save
plt.tight_layout()
plt.savefig("data/llg_quiver3d_step50.png")
plt.close()
