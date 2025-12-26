#!/usr/bin/env python3
"""
Phase C: Quantitative Analysis & Evaluation
Evaluate VIO trajectories against ground truth using the evo package.
"""

import os
import sys

# Set matplotlib backend BEFORE any other imports
os.environ['MPLBACKEND'] = 'Agg'

import argparse
import copy
import pandas as pd
import numpy as np
from pathlib import Path
from evo.core import sync
from evo.core.trajectory import PoseTrajectory3D
from evo.core.metrics import PoseRelation, Unit
from evo.tools import file_interface
from evo.core import lie_algebra as lie
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

# Define colors for consistency
COLORS = {
    'gt': '#1f77b4',      # Blue
    'est': '#ff7f0e',     # Orange
    'error': '#d62728'    # Red
}


def load_euroc_groundtruth(gt_file):
    """Load EuRoC ground truth data and convert to PoseTrajectory3D."""
    print(f"Loading ground truth from: {gt_file}")
    
    # EuRoC format: timestamp, px, py, pz, qw, qx, qy, qz, vx, vy, vz, bwx, bwy, bwz, bax, bay, baz
    df = pd.read_csv(gt_file, comment='#')
    
    # Extract timestamp and pose columns
    timestamps = df.iloc[:, 0].values / 1e9  # Convert nanoseconds to seconds
    positions = df.iloc[:, 1:4].values  # px, py, pz
    
    # Quaternions in EuRoC: qw, qx, qy, qz (columns 4-7)
    quaternions = df.iloc[:, [4, 5, 6, 7]].values  # qw, qx, qy, qz
    
    traj = PoseTrajectory3D(
        positions_xyz=positions,
        orientations_quat_wxyz=quaternions,
        timestamps=timestamps
    )
    
    print(f"  Loaded {len(timestamps)} poses")
    print(f"  Time range: {timestamps[0]:.3f}s - {timestamps[-1]:.3f}s")
    print(f"  Duration: {timestamps[-1] - timestamps[0]:.3f}s")
    
    return traj


def load_basalt_trajectory(traj_file):
    """Load Basalt trajectory and convert to PoseTrajectory3D."""
    print(f"Loading estimated trajectory from: {traj_file}")
    
    # Basalt format: timestamp, tx, ty, tz, qx, qy, qz, qw
    df = pd.read_csv(traj_file, comment='#', delim_whitespace=True)
    
    timestamps = df.iloc[:, 0].values  # Already in seconds
    positions = df.iloc[:, 1:4].values  # tx, ty, tz
    
    # Quaternions in Basalt: qx, qy, qz, qw (columns 4-7)
    quat_basalt = df.iloc[:, 4:8].values  # qx, qy, qz, qw
    
    # Convert to wxyz format for evo
    quaternions = np.zeros_like(quat_basalt)
    quaternions[:, 0] = quat_basalt[:, 3]  # qw
    quaternions[:, 1] = quat_basalt[:, 0]  # qx
    quaternions[:, 2] = quat_basalt[:, 1]  # qy
    quaternions[:, 3] = quat_basalt[:, 2]  # qz
    
    traj = PoseTrajectory3D(
        positions_xyz=positions,
        orientations_quat_wxyz=quaternions,
        timestamps=timestamps
    )
    
    print(f"  Loaded {len(timestamps)} poses")
    print(f"  Time range: {timestamps[0]:.3f}s - {timestamps[-1]:.3f}s")
    print(f"  Duration: {timestamps[-1] - timestamps[0]:.3f}s")
    
    return traj


def compute_ate(traj_ref, traj_est):
    """Compute Absolute Trajectory Error (ATE) with SE(3) Umeyama alignment."""
    from evo.core import metrics
    import copy
    
    print("\n=== Computing ATE (Absolute Trajectory Error) ===")
    
    # Synchronize trajectories
    traj_ref_sync, traj_est_sync = sync.associate_trajectories(traj_ref, traj_est)
    
    print(f"Synchronized trajectories: {len(traj_ref_sync.timestamps)} poses")
    
    # CRITICAL: Align trajectories using SE(3) Umeyama alignment (no scale correction)
    # This removes the systematic offset due to calibration errors
    print("Applying SE(3) Umeyama alignment...")
    traj_est_sync.align(traj_ref_sync, correct_scale=False, correct_only_scale=False)
    
    # Compute ATE after alignment
    ate_metric = metrics.APE(metrics.PoseRelation.translation_part)
    ate_metric.process_data((traj_ref_sync, traj_est_sync))
    
    ate_stats = ate_metric.get_all_statistics()
    
    print(f"\nATE Statistics (with SE(3) alignment):")
    print(f"  RMSE:   {ate_stats['rmse']:.6f} m")
    print(f"  Mean:   {ate_stats['mean']:.6f} m")
    print(f"  Median: {ate_stats['median']:.6f} m")
    print(f"  Std:    {ate_stats['std']:.6f} m")
    print(f"  Min:    {ate_stats['min']:.6f} m")
    print(f"  Max:    {ate_stats['max']:.6f} m")
    
    return ate_metric, traj_ref_sync, traj_est_sync


def compute_rpe(traj_ref, traj_est, delta=1.0, delta_unit=Unit.meters):
    """Compute Relative Pose Error (RPE) with SE(3) alignment."""
    from evo.core import metrics
    import copy
    
    print("\n=== Computing RPE (Relative Pose Error) ===")
    print(f"Delta: {delta} {delta_unit.value}")
    
    # Synchronize trajectories
    traj_ref_sync, traj_est_sync = sync.associate_trajectories(traj_ref, traj_est)
    
    # Make copies for alignment (RPE also benefits from alignment)
    traj_ref_copy = copy.deepcopy(traj_ref_sync)
    traj_est_copy = copy.deepcopy(traj_est_sync)
    
    # Align trajectories
    traj_est_copy.align(traj_ref_copy, correct_scale=False, correct_only_scale=False)
    
    # Compute RPE
    rpe_metric = metrics.RPE(
        pose_relation=metrics.PoseRelation.translation_part,
        delta=delta,
        delta_unit=delta_unit,
        all_pairs=False
    )
    rpe_metric.process_data((traj_ref_copy, traj_est_copy))
    
    rpe_stats = rpe_metric.get_all_statistics()
    
    print(f"\nRPE Statistics (translation, with alignment):")
    print(f"  RMSE:   {rpe_stats['rmse']:.6f} m")
    print(f"  Mean:   {rpe_stats['mean']:.6f} m")
    print(f"  Median: {rpe_stats['median']:.6f} m")
    print(f"  Std:    {rpe_stats['std']:.6f} m")
    print(f"  Min:    {rpe_stats['min']:.6f} m")
    print(f"  Max:    {rpe_stats['max']:.6f} m")
    
    return rpe_metric


def plot_trajectories_3d(traj_ref, traj_est, output_path, dataset_name):
    """Plot 3D trajectory comparison."""
    print(f"\nGenerating 3D trajectory plot...")
    
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot ground truth
    ax.plot(traj_ref.positions_xyz[:, 0],
            traj_ref.positions_xyz[:, 1],
            traj_ref.positions_xyz[:, 2],
            color=COLORS['gt'], label='Ground Truth', linewidth=2, alpha=0.8)
    
    # Plot estimated
    ax.plot(traj_est.positions_xyz[:, 0],
            traj_est.positions_xyz[:, 1],
            traj_est.positions_xyz[:, 2],
            color=COLORS['est'], label='Estimated', linewidth=2, alpha=0.8)
    
    # Mark start and end
    ax.scatter(traj_ref.positions_xyz[0, 0],
               traj_ref.positions_xyz[0, 1],
               traj_ref.positions_xyz[0, 2],
               color='green', s=100, marker='o', label='Start', zorder=5)
    
    ax.scatter(traj_ref.positions_xyz[-1, 0],
               traj_ref.positions_xyz[-1, 1],
               traj_ref.positions_xyz[-1, 2],
               color='red', s=100, marker='s', label='End', zorder=5)
    
    ax.set_xlabel('X [m]', fontsize=12)
    ax.set_ylabel('Y [m]', fontsize=12)
    ax.set_zlabel('Z [m]', fontsize=12)
    ax.set_title(f'3D Trajectory Comparison - {dataset_name}', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"  Saved to: {output_path}")
    plt.close()


def plot_trajectories_2d(traj_ref, traj_est, output_path, dataset_name):
    """Plot 2D top-down trajectory comparison."""
    print(f"\nGenerating 2D trajectory plot...")
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Plot ground truth
    ax.plot(traj_ref.positions_xyz[:, 0],
            traj_ref.positions_xyz[:, 1],
            color=COLORS['gt'], label='Ground Truth', linewidth=2, alpha=0.8)
    
    # Plot estimated
    ax.plot(traj_est.positions_xyz[:, 0],
            traj_est.positions_xyz[:, 1],
            color=COLORS['est'], label='Estimated', linewidth=2, alpha=0.8)
    
    # Mark start and end
    ax.scatter(traj_ref.positions_xyz[0, 0],
               traj_ref.positions_xyz[0, 1],
               color='green', s=100, marker='o', label='Start', zorder=5)
    
    ax.scatter(traj_ref.positions_xyz[-1, 0],
               traj_ref.positions_xyz[-1, 1],
               color='red', s=100, marker='s', label='End', zorder=5)
    
    ax.set_xlabel('X [m]', fontsize=12)
    ax.set_ylabel('Y [m]', fontsize=12)
    ax.set_title(f'2D Trajectory Comparison (Top View) - {dataset_name}', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.axis('equal')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"  Saved to: {output_path}")
    plt.close()


def plot_ate_over_time(ate_metric, traj_ref_sync, output_path, dataset_name):
    """Plot ATE error over time."""
    print(f"\nGenerating ATE over time plot...")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Extract errors
    errors = ate_metric.error
    timestamps = traj_ref_sync.timestamps
    
    # Normalize timestamps to start from 0
    timestamps_rel = timestamps - timestamps[0]
    
    # Plot 1: Error magnitude over time
    ax1.plot(timestamps_rel, errors, color=COLORS['error'], linewidth=1.5, alpha=0.8)
    ax1.axhline(y=np.mean(errors), color='black', linestyle='--', 
                label=f'Mean: {np.mean(errors):.4f} m', linewidth=2)
    ax1.axhline(y=np.sqrt(np.mean(errors**2)), color='blue', linestyle='--',
                label=f'RMSE: {np.sqrt(np.mean(errors**2)):.4f} m', linewidth=2)
    ax1.set_xlabel('Time [s]', fontsize=12)
    ax1.set_ylabel('ATE [m]', fontsize=12)
    ax1.set_title(f'Absolute Trajectory Error Over Time - {dataset_name}', 
                  fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Cumulative error distribution
    sorted_errors = np.sort(errors)
    cumulative = np.arange(1, len(sorted_errors) + 1) / len(sorted_errors) * 100
    
    ax2.plot(sorted_errors, cumulative, color=COLORS['error'], linewidth=2)
    ax2.axvline(x=np.median(errors), color='green', linestyle='--',
                label=f'Median: {np.median(errors):.4f} m', linewidth=2)
    ax2.axvline(x=np.percentile(errors, 95), color='orange', linestyle='--',
                label=f'95th percentile: {np.percentile(errors, 95):.4f} m', linewidth=2)
    ax2.set_xlabel('ATE [m]', fontsize=12)
    ax2.set_ylabel('Cumulative Percentage [%]', fontsize=12)
    ax2.set_title('Cumulative Error Distribution', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"  Saved to: {output_path}")
    plt.close()


def plot_rpe_over_time(rpe_metric, traj_ref_sync, output_path, dataset_name):
    """Plot RPE error over time."""
    print(f"\nGenerating RPE over time plot...")
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Extract errors
    errors = rpe_metric.error
    timestamps = traj_ref_sync.timestamps[: len(errors)]
    
    # Normalize timestamps to start from 0
    timestamps_rel = timestamps - timestamps[0]
    
    ax.plot(timestamps_rel, errors, color=COLORS['error'], linewidth=1.5, alpha=0.8)
    ax.axhline(y=np.mean(errors), color='black', linestyle='--',
               label=f'Mean: {np.mean(errors):.4f} m', linewidth=2)
    ax.axhline(y=np.sqrt(np.mean(errors**2)), color='blue', linestyle='--',
               label=f'RMSE: {np.sqrt(np.mean(errors**2)):.4f} m', linewidth=2)
    ax.set_xlabel('Time [s]', fontsize=12)
    ax.set_ylabel('RPE [m]', fontsize=12)
    ax.set_title(f'Relative Pose Error Over Time - {dataset_name}', 
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"  Saved to: {output_path}")
    plt.close()


def plot_xyz_errors(traj_ref, traj_est, output_path, dataset_name):
    """Plot X, Y, Z position errors over time."""
    print(f"\nGenerating XYZ error plot...")
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12))
    
    # Compute position differences
    pos_diff = traj_est.positions_xyz - traj_ref.positions_xyz
    timestamps_rel = traj_ref.timestamps - traj_ref.timestamps[0]
    
    # X error
    ax1.plot(timestamps_rel, pos_diff[:, 0], color='r', linewidth=1.5, alpha=0.8)
    ax1.axhline(y=0, color='black', linestyle='--', linewidth=1)
    ax1.set_ylabel('X Error [m]', fontsize=12)
    ax1.set_title(f'Position Errors Over Time - {dataset_name}', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.text(0.02, 0.95, f'RMSE: {np.sqrt(np.mean(pos_diff[:, 0]**2)):.4f} m',
             transform=ax1.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Y error
    ax2.plot(timestamps_rel, pos_diff[:, 1], color='g', linewidth=1.5, alpha=0.8)
    ax2.axhline(y=0, color='black', linestyle='--', linewidth=1)
    ax2.set_ylabel('Y Error [m]', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.text(0.02, 0.95, f'RMSE: {np.sqrt(np.mean(pos_diff[:, 1]**2)):.4f} m',
             transform=ax2.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Z error
    ax3.plot(timestamps_rel, pos_diff[:, 2], color='b', linewidth=1.5, alpha=0.8)
    ax3.axhline(y=0, color='black', linestyle='--', linewidth=1)
    ax3.set_xlabel('Time [s]', fontsize=12)
    ax3.set_ylabel('Z Error [m]', fontsize=12)
    ax3.grid(True, alpha=0.3)
    ax3.text(0.02, 0.95, f'RMSE: {np.sqrt(np.mean(pos_diff[:, 2]**2)):.4f} m',
             transform=ax3.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"  Saved to: {output_path}")
    plt.close()


def save_results_json(results, output_path):
    """Save evaluation results to JSON file."""
    import json
    
    print(f"\nSaving results to: {output_path}")
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print("  Done!")


def evaluate_dataset(dataset_name, traj_file, gt_file, output_dir):
    """Evaluate a single dataset."""
    
    print(f"\n{'='*80}")
    print(f"EVALUATING: {dataset_name}")
    print(f"{'='*80}")
    
    # Create output directory
    dataset_output_dir = Path(output_dir) / dataset_name.lower().replace(' ', '_')
    dataset_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load trajectories
    traj_gt = load_euroc_groundtruth(gt_file)
    traj_est = load_basalt_trajectory(traj_file)
    
    # Compute metrics
    ate_metric, traj_ref_sync, traj_est_sync = compute_ate(traj_gt, traj_est)
    rpe_metric = compute_rpe(traj_gt, traj_est, delta=1.0, delta_unit=Unit.meters)
    
    # Generate plots
    plot_trajectories_3d(traj_ref_sync, traj_est_sync,
                         dataset_output_dir / 'trajectory_3d.png',
                         dataset_name)
    
    plot_trajectories_2d(traj_ref_sync, traj_est_sync,
                         dataset_output_dir / 'trajectory_2d.png',
                         dataset_name)
    
    plot_ate_over_time(ate_metric, traj_ref_sync,
                       dataset_output_dir / 'ate_over_time.png',
                       dataset_name)
    
    plot_rpe_over_time(rpe_metric, traj_ref_sync,
                       dataset_output_dir / 'rpe_over_time.png',
                       dataset_name)
    
    plot_xyz_errors(traj_ref_sync, traj_est_sync,
                    dataset_output_dir / 'xyz_errors.png',
                    dataset_name)
    
    # Collect results
    ate_stats = ate_metric.get_all_statistics()
    rpe_stats = rpe_metric.get_all_statistics()
    
    results = {
        'dataset': dataset_name,
        'trajectory_file': str(traj_file),
        'groundtruth_file': str(gt_file),
        'num_poses_original_gt': len(traj_gt.timestamps),
        'num_poses_original_est': len(traj_est.timestamps),
        'num_poses_synchronized': len(traj_ref_sync.timestamps),
        'duration_seconds': float(traj_ref_sync.timestamps[-1] - traj_ref_sync.timestamps[0]),
        'ate': {
            'rmse': float(ate_stats['rmse']),
            'mean': float(ate_stats['mean']),
            'median': float(ate_stats['median']),
            'std': float(ate_stats['std']),
            'min': float(ate_stats['min']),
            'max': float(ate_stats['max'])
        },
        'rpe': {
            'rmse': float(rpe_stats['rmse']),
            'mean': float(rpe_stats['mean']),
            'median': float(rpe_stats['median']),
            'std': float(rpe_stats['std']),
            'min': float(rpe_stats['min']),
            'max': float(rpe_stats['max'])
        }
    }
    
    # Save results
    save_results_json(results, dataset_output_dir / 'evaluation_results.json')
    
    # --- UPDATED: Save Root Cause Analysis to file ---
    # Передаем dataset_output_dir
    analyze_worst_errors(ate_metric, traj_ref_sync, dataset_name, dataset_output_dir)
    
    print(f"\n{'='*80}")
    print(f"EVALUATION COMPLETE: {dataset_name}")
    print(f"Results saved to: {dataset_output_dir}")
    print(f"{'='*80}\n")
    
    return results

def analyze_worst_errors(ate_metric, traj_ref_sync, dataset_name, output_dir, top_n=5):
    """
    Saves Root Cause Analysis to a text file.
    Finds timestamps with the largest errors.
    """
    output_file = Path(output_dir) / "analysis_report.txt"
    
    print(f"Generating analysis report: {output_file}")
    
    errors = ate_metric.error
    timestamps = traj_ref_sync.timestamps
    
    # Get indices of the top N largest errors
    worst_indices = np.argsort(errors)[-top_n:][::-1]
    
    with open(output_file, 'w') as f:
        f.write(f"ROOT CAUSE ANALYSIS REPORT\n")
        f.write(f"Dataset: {dataset_name}\n")
        f.write(f"========================================\n\n")
        
        f.write(f"TOP {top_n} WORST TRACKING MOMENTS:\n")
        f.write(f"----------------------------------------\n")
        for i in worst_indices:
            t = timestamps[i]
            err = errors[i]
            rel_t = t - timestamps[0]
            # Пишем время и ошибку
            f.write(f"Timestamp: {t:.3f} (Time from start: {rel_t:.2f}s) --> Error: {err:.4f} m\n")
        
        f.write(f"\nAUTOMATED DIAGNOSIS:\n")
        f.write(f"----------------------------------------\n")
        
        max_error = np.max(errors)
        rmse = np.sqrt(np.mean(errors**2))
        
        f.write(f"Max Error: {max_error:.4f} m\n")
        f.write(f"RMSE:      {rmse:.4f} m\n\n")
        
        if max_error < 0.15:
            f.write("CONCLUSION: STABLE.\n")
            f.write("The system demonstrates robust tracking. Deviations are within acceptable limits.\n")
        elif max_error < 0.50:
             f.write("CONCLUSION: MINOR DRIFT.\n")
             f.write("Tracking is generally good but has moments of drift.\n")
             f.write("Suggested Action: Check timestamps above for fast motion or dynamic objects.\n")
        else:
            f.write("CONCLUSION: CRITICAL FAILURE DETECTED.\n")
            f.write("High trajectory divergence observed.\n")
            f.write("Potential Causes:\n")
            f.write("1. Motion Blur (Aggressive rotation)\n")
            f.write("2. Low Texture environment (white walls/floor)\n")
            f.write("3. IMU saturation or calibration mismatch\n")

    print(f"  -> Saved analysis to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Evaluate VIO trajectories')
    parser.add_argument('--dataset', choices=['mh_01', 'v1_03', 'all'], default='all',
                        help='Dataset to evaluate')
    parser.add_argument('--output-dir', default='/workspace/results/evaluation',
                        help='Output directory for results')
    
    args = parser.parse_args()
    
    # Dataset configurations
    datasets = {
        'mh_01': {
            'name': 'MH_01_easy',
            'traj_file': '/workspace/results/trajectories/traj_mh_01_easy.csv',
            'gt_file': '/workspace/data/MH_01_easy/mav0/state_groundtruth_estimate0/data.csv'
        },
        'v1_03': {
            'name': 'V1_03_difficult',
            'traj_file': '/workspace/results/trajectories/traj_v1_03_difficult.csv',
            'gt_file': '/workspace/data/V1_03_difficult/mav0/state_groundtruth_estimate0/data.csv'
        }
    }
    
    # Run evaluations
    all_results = []
    
    if args.dataset == 'all':
        datasets_to_eval = datasets.keys()
    else:
        datasets_to_eval = [args.dataset]
    
    for dataset_key in datasets_to_eval:
        config = datasets[dataset_key]
        
        # Check if files exist
        if not Path(config['traj_file']).exists():
            print(f"ERROR: Trajectory file not found: {config['traj_file']}")
            continue
        if not Path(config['gt_file']).exists():
            print(f"ERROR: Ground truth file not found: {config['gt_file']}")
            continue
        
        results = evaluate_dataset(
            config['name'],
            config['traj_file'],
            config['gt_file'],
            args.output_dir
        )
        all_results.append(results)
    
    # Save combined results
    if all_results:
        combined_output = Path(args.output_dir) / 'all_results.json'
        save_results_json(all_results, combined_output)
        
        # Print summary
        print(f"\n{'='*80}")
        print("EVALUATION SUMMARY")
        print(f"{'='*80}")
        for result in all_results:
            print(f"\n{result['dataset']}:")
            print(f"  ATE RMSE: {result['ate']['rmse']:.6f} m")
            print(f"  RPE RMSE: {result['rpe']['rmse']:.6f} m")
            print(f"  Duration: {result['duration_seconds']:.2f} s")
            print(f"  Poses: {result['num_poses_synchronized']}")
        print(f"\n{'='*80}\n")


if __name__ == '__main__':
    main()
