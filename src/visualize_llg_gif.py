import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import animation

# ====== CONSTANTS ======
FOLDER = "data_llg"  # path relative to root folder
CSV_PATTERN = r"^step_\d+\.csv$"
OUTPUT_PATH = "llg_magnetization.gif"
FPS = 20
ARROW_LENGTH_RATIO = 0.4

# ====== Load CSV files ======
file_list = sorted(
    [f for f in os.listdir(FOLDER) if re.match(CSV_PATTERN, f)],
    key=lambda x: int(re.findall(r"\d+", x)[0])
)

print(f"Found {len(file_list)} CSV files:")
for f in file_list:
    print(" -", f)

if not file_list:
    raise FileNotFoundError(f"No CSV files matching {CSV_PATTERN} in {FOLDER}")

frames = []
for filename in file_list:
    file_path = os.path.join(FOLDER, filename)
    df = pd.read_csv(file_path, header=None, delim_whitespace=True)
    frames.append(df.to_numpy())

# ====== Prepare Plot ======
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

X, Y, Z = frames[0][:, 0], frames[0][:, 1], frames[0][:, 2]
U, V, W = frames[0][:, 3], frames[0][:, 4], frames[0][:, 5]

quiver = ax.quiver(X, Y, Z, U, V, W, length=ARROW_LENGTH_RATIO, normalize=True, color='blue')

# Optional: draw disk
theta = np.linspace(0, 2 * np.pi, 100)
x_disk = np.cos(theta)
y_disk = np.sin(theta)
z_disk = np.zeros_like(x_disk)
ax.plot_trisurf(x_disk, y_disk, z_disk, color='lightgreen', alpha=0.3)

ax.set_xlim([-1, 1])
ax.set_ylim([-1, 1])
ax.set_zlim([-1, 1])
ax.set_title("LLG Magnetization Evolution")

# ====== Animation Update ======
def update_quiver(i):
    global quiver
    quiver.remove()
    data = frames[i]
    quiver = ax.quiver(
        data[:, 0], data[:, 1], data[:, 2],
        data[:, 3], data[:, 4], data[:, 5],
        length=ARROW_LENGTH_RATIO, normalize=True, color='blue'
    )
    ax.set_title(f"LLG Magnetization Evolution — step {i}")
    return quiver,

# ====== Create and Save Animation ======
ani = animation.FuncAnimation(fig, update_quiver, frames=len(frames), blit=False)
ani.save(OUTPUT_PATH, writer='pillow', fps=FPS)
print(f"\n✅ GIF saved to: {OUTPUT_PATH}")

