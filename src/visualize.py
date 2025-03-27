import pandas as pd
import matplotlib.pyplot as plt
import os

def generate_visualizations():
    print("Generating visualization...")
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(project_root, "data", "solution_data.csv")
    output_path = os.path.join(project_root, "data", "heat_final.png")

    df = pd.read_csv(data_path)
    last_t = df["time"].max()
    sub_df = df[df["time"] == last_t]

    fig, ax = plt.subplots()
    scatter = ax.scatter(sub_df["x"], sub_df["y"], c=sub_df["u"], cmap="hot", s=20)
    ax.set_title(f"Heat distribution at final time t = {last_t}")
    plt.colorbar(scatter)
    plt.savefig(output_path)
    print(f"Saved final frame to: {output_path}")
