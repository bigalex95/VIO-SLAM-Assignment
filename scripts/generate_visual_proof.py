import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import glob
from PIL import Image


def generate_visual_proof(traj_file, image_dir, output_file):
    print(f"Loading trajectory from {traj_file}...")
    # Load trajectory (TUM format: timestamp tx ty tz qx qy qz qw)
    try:
        traj_data = pd.read_csv(
            traj_file,
            sep="\s+",
            comment="#",
            header=None,
            names=["timestamp", "tx", "ty", "tz", "qx", "qy", "qz", "qw"],
        )
    except Exception as e:
        print(f"Error loading trajectory: {e}")
        return

    print(f"Found {len(traj_data)} poses.")

    # Find a representative image (e.g., from the middle of the sequence)
    image_files = sorted(glob.glob(os.path.join(image_dir, "*.png")))
    if not image_files:
        print(f"No images found in {image_dir}")
        return

    # Pick an image roughly in the middle
    mid_idx = len(image_files) // 2
    target_image_path = image_files[mid_idx]
    target_ts_str = os.path.basename(target_image_path).split(".")[0]
    target_ts = float(target_ts_str)

    print(f"Selected image: {target_image_path}")

    # Find closest trajectory point
    # Timestamps in csv are seconds or nanoseconds?
    # CSV sample: 1.403636579763555765e+09 -> This is seconds (1.4e9)
    # Image filename: 1403636579763555584.png -> This is nanoseconds (1.4e18)

    # Convert CSV timestamps to nanoseconds to match filenames
    traj_timestamps_ns = traj_data["timestamp"] * 1e9

    # Find index of closest timestamp
    diff = np.abs(traj_timestamps_ns - target_ts)
    closest_idx = diff.idxmin()
    current_pose = traj_data.iloc[closest_idx]

    print(
        f"Closest pose at index {closest_idx}: {current_pose[['tx', 'ty', 'tz']].values}"
    )

    # Create the visualization
    fig = plt.figure(figsize=(16, 8))
    fig.suptitle("VIO-SLAM System Output - Visual Proof", fontsize=20)

    # Subplot 1: Camera View
    ax1 = fig.add_subplot(1, 2, 1)
    img = Image.open(target_image_path)
    ax1.imshow(img, cmap="gray")
    ax1.set_title(f"Camera Input (Frame: {target_ts_str})", fontsize=14)
    ax1.axis("off")

    # Overlay status text
    status_text = (
        f"Status: TRACKING\n"
        f"Pos: [{current_pose['tx']:.2f}, {current_pose['ty']:.2f}, {current_pose['tz']:.2f}]\n"
        f"Time: {current_pose['timestamp']:.3f} s"
    )
    ax1.text(
        20,
        40,
        status_text,
        color="lime",
        fontsize=12,
        fontweight="bold",
        bbox=dict(facecolor="black", alpha=0.5),
    )

    # Subplot 2: Trajectory Map (Top-Down)
    ax2 = fig.add_subplot(1, 2, 2)
    ax2.plot(
        traj_data["tx"],
        traj_data["ty"],
        "b-",
        label="Estimated Trajectory",
        linewidth=1,
    )
    ax2.plot(
        current_pose["tx"], current_pose["ty"], "ro", label="Current Pose", markersize=8
    )

    # Start point
    ax2.plot(
        traj_data["tx"].iloc[0],
        traj_data["ty"].iloc[0],
        "g^",
        label="Start",
        markersize=8,
    )

    ax2.set_title("Trajectory Estimate (Top-Down View)", fontsize=14)
    ax2.set_xlabel("X Position (m)")
    ax2.set_ylabel("Y Position (m)")
    ax2.grid(True)
    ax2.legend()
    ax2.axis("equal")

    plt.tight_layout()

    print(f"Saving visual proof to {output_file}...")
    plt.savefig(output_file, dpi=100)
    print("Done.")


if __name__ == "__main__":
    # Define paths
    workspace_root = "/home/bigalex95/Projects/challenges/VIO-SLAM-Assignment"
    traj_path = os.path.join(workspace_root, "results/trajectories/traj_mh_01_easy.csv")
    img_dir = os.path.join(workspace_root, "data/MH_01_easy/mav0/cam0/data")
    output_path = os.path.join(workspace_root, "results/visual_proof.png")

    generate_visual_proof(traj_path, img_dir, output_path)
