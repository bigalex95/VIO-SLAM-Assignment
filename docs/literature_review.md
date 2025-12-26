# Literature Review & Method Selection

## 1. Research & Comparison of SOTA VIO/SLAM Frameworks

State-of-the-art Visual-Inertial Odometry (VIO) and SLAM systems have evolved significantly. For a drone operating in GPS-denied environments (warehouses, tunnels), the system must balance accuracy, robustness to fast motion, and computational efficiency (SWaP - Size, Weight, and Power).

We compared five prominent open-source frameworks:

| Framework | Type | Backend | Loop Closure? | Compute Load | Robustness |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OpenVINS** | Filter (MSCKF) | EKF-based (Sliding Window) | Yes (secondary thread) | **Low** | High |
| **VINS-Mono** | Optimization | Nonlinear Optimization (Sliding Window) | Yes (4-DOF pose graph) | Medium | High |
| **ORB-SLAM3** | Optimization | Full Bundle Adjustment | Yes (Atlas multi-map) | High | **Very High** |
| **BASALT** | Optimization | Nonlinear Factor Recovery | Yes | Low-Medium | High |
| **Kimera** | Optimization | GTSAM (Factor Graph) | Yes (Kimera-RPGO) | High (with semantics) | High |

### Analysis

1.  **Computational Efficiency (Jetson suitability)**:
    *   **OpenVINS**: Being filter-based (MSCKF), it is computationally very efficient. It updates the state without maintaining a massive map of features in the state vector (marginalizing them out). This makes it ideal for embedded platforms like the Jetson.
    *   **ORB-SLAM3**: While extremely accurate, maintaining a global map and performing bundle adjustment can be CPU-intensive, potentially saturating a Jetson's CPU cores, especially in feature-rich environments.
    *   **Kimera**: The full pipeline (including mesh generation and semantics) is too heavy for a basic state estimation task on limited hardware, though the VIO frontend is comparable to VINS-Mono.

2.  **Robustness**:
    *   **ORB-SLAM3** is arguably the most robust to "kidnapping" and aggressive motion due to its multi-map system (Atlas).
    *   **OpenVINS** and **VINS-Mono** are also very robust for drone dynamics. OpenVINS specifically handles timing offsets and calibration online, which is critical for real-world sensor setups.

3.  **Loop Closure**:
    *   All candidates support loop closure. OpenVINS treats it as a loosely-coupled update, which is sufficient to correct drift over long trajectories without the heavy cost of global bundle adjustment.

## 2. Selection & Justification

**Selected Framework: OpenVINS**

### Technical Justification
We choose **OpenVINS** for this assignment for the following reasons:

1.  **Efficiency for Embedded Systems**: Drones have strict power and compute limits. OpenVINS's MSCKF (Multi-State Constraint Kalman Filter) approach provides excellent accuracy-to-compute ratio. It is lighter than optimization-based approaches like VINS-Mono or ORB-SLAM3 while delivering comparable accuracy for odometry metrics.
2.  **Online Calibration**: Drones suffer from vibrations and temperature changes. OpenVINS excels at online extrinsic and intrinsic calibration, as well as time-offset estimation, ensuring the system remains robust even if initial calibration is slightly off.
3.  **Docs & Reproducibility**: OpenVINS has excellent documentation and container support, perfectly matching the assignment's requirement for a reproducible environment.

### Suitability for Drone Platform
The "drone platform" context implies:
*   **Fast Dynamics**: High frequency IMU processing (supported well by OpenVINS).
*   **Limited Compute**: Need to leave CPU/GPU headroom for other tasks (path planning, obstacle avoidance). OpenVINS leaves more resources free than ORB-SLAM3.
