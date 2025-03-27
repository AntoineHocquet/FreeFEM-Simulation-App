# src/visualize_gif.py
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.tri as tri
from matplotlib.animation import FuncAnimation

def generate_gif():
    print("Generating heat equation animation...")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(project_root, "data", "solution_data.csv")
    gif_path = os.path.join(project_root, "data", "heat_equation_simulation.gif")

    # Load the CSV data
    data = pd.read_csv(csv_path)

    # Extract unique time steps
    time_steps = data['time'].unique()

    # Extract mesh points from the first time step
    mesh_points = data[data['time'] == time_steps[0]]
    x = mesh_points['x'].values
    y = mesh_points['y'].values

    # Compute global min and max for color scale
    u_min = data['u'].min()
    u_max = data['u'].max()

    # Prepare the triangulation
    triang = tri.Triangulation(x, y)

    # Initialize the plot
    fig, ax = plt.subplots(figsize=(6, 5))

    # Update function for the animation
    def update(frame):
        current_data = data[data['time'] == time_steps[frame]]
        ax.clear()
        contour = ax.tricontourf(
            triang, current_data['u'], cmap='inferno',
            vmin=u_min, vmax=u_max
        )
        ax.set_title(f"Heat Equation at Time = {time_steps[frame]:.2f}s")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        #return contour.collections

    # Create the animation
    anim = FuncAnimation(fig, update, frames=len(time_steps), interval=100, repeat=False)

    # Save the animation as a GIF
    anim.save(gif_path, writer='imagemagick')

    # Close the plot after saving
    plt.close()

    print(f"Animation saved to: {gif_path}")
