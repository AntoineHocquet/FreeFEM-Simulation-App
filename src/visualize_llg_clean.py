import pandas as pd
import matplotlib.pyplot as plt
import os
import argparse
from mpl_toolkits.mplot3d import Axes3D

ARROW_LENGTH_RATIO = 0.4

def load_frame(folder_path, step):
    file_path = os.path.join(folder_path, f"step_{step}.csv")
    return pd.read_csv(file_path, header=None, delim_whitespace=True)

def plot_vector_field_3d(frame, step, output_path):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    x, y = frame[0], frame[1]
    u, v, w = frame[3], frame[4], frame[5]
    z = [0] * len(x)  # flat disk

    ax.quiver(x, y, z, u, v, w, color='b', length=ARROW_LENGTH_RATIO, normalize=True)
    ax.set_title(f'Magnetization vector field at step {step}')
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_zlim([-1, 1])

    ax.plot_trisurf(x, y, z, color='lightgreen', alpha=0.3)
    plt.savefig(output_path)
    print(f"✅ Plot saved to {output_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--step', type=int, required=True, help='Time step to visualize')
    parser.add_argument('--folder', type=str, default='edp/data_llg', help='Folder where the CSV files are located')
    parser.add_argument('--output', type=str, help='Output path for the PNG image')
    args = parser.parse_args()

    frame = load_frame(args.folder, args.step)

    # Default output path if none provided
    output_path = args.output or os.path.join("data", f"llg_quiver3d_step{args.step}.png")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plot_vector_field_3d(frame, args.step, output_path)

if __name__ == '__main__':
    main()
