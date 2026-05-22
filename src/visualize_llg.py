# src/visualize_llg_3d.py
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_LLG = os.path.join(PROJECT_ROOT, "data", "data_llg")

# Load a single step (default 0; pass an integer to pick another)
step = int(sys.argv[1]) if len(sys.argv) > 1 else 0
df = pd.read_csv(os.path.join(DATA_LLG, f"step_{step}.csv"), header=None, sep=r"\s+")

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
ax.set_title(f"Magnetization vector field at step {step}")

# Save
plt.tight_layout()
out_path = os.path.join(PROJECT_ROOT, "data", f"llg_quiver3d_step{step}.png")
plt.savefig(out_path)
plt.close()
print(f"Saved {out_path}")
