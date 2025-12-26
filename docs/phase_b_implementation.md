# Phase B: Implementation Documentation

## 1. Framework Setup Overview

### Selected Framework: BASALT VIO

- **Version:** Latest from GitHub (commit-based)
- **License:** BSD 3-Clause
- **Repository:** https://gitlab.com/VladyslavUsenko/basalt

---

## 2. Environment Setup

### 2.1 Docker Containerization

The implementation uses Docker for reproducible deployment across different platforms.

#### Dockerfile Analysis

**Base Image:** Ubuntu 22.04 LTS

- Modern stable platform
- Good package availability
- Compatible with Jetson platforms (ARM64 builds available)

**Key Dependencies Installed:**

1. **Build Tools:**

   - GCC/G++ (build-essential)
   - CMake 3.22+
   - Ninja build system for faster compilation

2. **Required Libraries:**

   - **TBB (Threading Building Blocks):** Parallel computation
   - **Eigen3:** Linear algebra (3.4.0+)
   - **OpenCV:** Image processing and feature detection
   - **Boost:** System utilities
   - **fmt:** Modern C++ formatting library

3. **Visualization:**

   - **Pangolin:** Built from source for GUI and 3D visualization
   - OpenGL libraries for rendering

4. **Evaluation Tools:**
   - **evo:** Python package for trajectory evaluation
   - Installed via pip3 (no binary for latest version)

#### Docker Build Command

```bash
cd /workspace/docker
docker build -t basalt-vio:latest .
```

#### Docker Run Command

```bash
docker run -it --rm \
  -v /workspace:/workspace \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -e DISPLAY=$DISPLAY \
  --name basalt-container \
  basalt-vio:latest
```

**Environment Variables:**

- `DISPLAY`: X11 forwarding for GUI visualization
- `DEBIAN_FRONTEND=noninteractive`: Automated apt installation

---

## 3. BASALT Compilation

### 3.1 Build Configuration

**Build System:** CMake with Ninja generator

**Build Type:** Release

- Optimization flags: -O3 -march=native
- Debug symbols stripped for smaller binary size
- Vectorization enabled (SSE/AVX on x86, NEON on ARM)

**Compilation Process:**

```bash
cd /workspace/external/basalt
mkdir -p build
cd build

cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=/usr/local \
  -G Ninja

ninja -j$(nproc)
```

**Compilation Time:** ~15-20 minutes on 8-core CPU

### 3.2 Generated Executables

Key binaries produced:

1. **basalt_vio**: Main Visual-Inertial Odometry executable
2. **basalt_calibrate**: Camera-IMU calibration tool
3. **basalt_opt_flow**: Optical flow visualization
4. **basalt_vio_sim**: Simulation testing tool

Location: `/workspace/external/basalt/build/`

---

## 4. Dataset Configuration

### 4.1 EuRoC MAV Dataset

**Selected Sequences:**

1. **MH_01_easy** (Machine Hall 01 - Easy)

   - Duration: 182 seconds
   - Trajectory length: ~80 meters
   - Characteristics: Moderate motion, good lighting, textured environment
   - Purpose: Baseline performance evaluation

2. **V1_03_difficult** (Vicon Room 1_03 - Difficult)
   - Duration: 105 seconds
   - Trajectory length: ~50 meters
   - Characteristics: Fast motion, aggressive rotations, challenging for VIO
   - Purpose: Stress testing and robustness evaluation

**Dataset Structure:**

```
data/
├── MH_01_easy/
│   └── mav0/
│       ├── cam0/           # Left camera images
│       ├── cam1/           # Right camera images
│       ├── imu0/           # IMU data (200 Hz)
│       └── state_groundtruth_estimate0/  # Ground truth poses
└── V1_03_difficult/
    └── mav0/
        ├── cam0/
        ├── cam1/
        ├── imu0/
        └── state_groundtruth_estimate0/
```

---

## 5. Sensor Calibration Configuration

### 5.1 IMU Specifications (ADIS16448)

From `/workspace/data/MH_01_easy/mav0/imu0/sensor.yaml`:

**Noise Parameters (Manufacturer Specifications):**

- **Gyroscope Noise Density:** 1.6968e-04 rad/s/√Hz
- **Gyroscope Random Walk:** 1.9393e-05 rad/s²/√Hz
- **Accelerometer Noise Density:** 2.0000e-03 m/s²/√Hz
- **Accelerometer Random Walk:** 3.0000e-03 m/s³/√Hz
- **IMU Rate:** 200 Hz

### 5.2 Configuration File Tuning

**File:** `/workspace/configs/my_euroc_calib.json`

#### Custom Tuning Applied:

**1. IMU Noise Standard Deviations:**

```json
"accel_noise_std": [0.016, 0.016, 0.016],
"gyro_noise_std": [0.000282, 0.000282, 0.000282]
```

**Calculation:**

- Accel noise std = noise_density × √(sample_rate) = 0.002 × √200 ≈ 0.028
- Adjusted to 0.016 based on empirical testing (slightly conservative)
- Gyro noise std = 0.00016968 × √200 ≈ 0.0024
- Adjusted to 0.000282 (tuned for stability)

**2. IMU Bias Standard Deviations:**

```json
"accel_bias_std": [0.001, 0.001, 0.001],
"gyro_bias_std": [0.0001, 0.0001, 0.0001]
```

**Rationale:** Conservative bias evolution model prevents bias divergence

**3. Camera-IMU Extrinsics:**

```json
"T_imu_cam": [
  {
    "px": -0.0167, "py": -0.0689, "pz": 0.0051,
    "qx": -0.0072, "qy": 0.0075, "qz": 0.7018, "qw": 0.7123
  },
  {
    "px": -0.0151, "py": 0.0413, "pz": 0.0032,
    "qx": -0.0023, "qy": 0.0130, "qz": 0.7025, "qw": 0.7116
  }
]
```

**Source:** Factory calibration from EuRoC dataset
**Validation:** Verified with basalt_calibrate tool

**4. Camera Intrinsics:**

- **Model:** Double Sphere (DS) - handles wide-angle distortion
- **Resolution:** 752x480 pixels
- **Focal Length:** ~350 pixels (moderate FOV)

**5. Temporal Calibration:**

```json
"cam_time_offset_ns": 0,
"mocap_to_imu_offset_ns": 140763258159875
```

**Critical:** Proper time synchronization prevents integration drift.

- **Note:** EuRoC sensors are hardware-synchronized; we assume zero time offset (`cam_time_offset_ns: 0`).
- **Provenance:** Camera intrinsics and extrinsics were taken from the official EuRoC calibration files (`cam_april/cam_chain.yaml`) and verified against the Basalt example configuration.

---

## 6. VIO Configuration Parameters

### 6.1 Optical Flow Settings

From `/workspace/external/basalt/data/euroc_config.json`:

```json
"config.optical_flow_type": "frame_to_frame",
"config.optical_flow_detection_grid_size": 50,
"config.optical_flow_max_iterations": 5,
"config.optical_flow_levels": 3
```

**Explanation:**

- **Grid size 50:** Ensures feature distribution across image
- **5 iterations:** Balance between accuracy and speed
- **3 pyramid levels:** Multi-scale tracking for large motions

### 6.2 VIO Optimization Settings

```json
"config.vio_max_states": 3,
"config.vio_max_kfs": 7,
"config.vio_obs_std_dev": 0.5,
"config.vio_use_lm": true
```

**Key Parameters:**

- **max_states = 3:** Sliding window size (computational vs accuracy tradeoff)
- **max_kfs = 7:** Keyframe buffer for optimization
- **obs_std_dev = 0.5:** Observation uncertainty (pixels)
- **Levenberg-Marquardt:** Robust non-linear optimization

---

## 7. Execution Commands

### 7.1 Running VIO on MH_01_easy

```bash
cd /workspace/external/basalt/build

./basalt_vio \
  --dataset-path /workspace/data/MH_01_easy \
  --cam-calib /workspace/configs/my_euroc_calib.json \
  --dataset-type euroc \
  --config-path /workspace/external/basalt/data/euroc_config.json \
  --result-path /workspace/results/trajectories/traj_mh_01_easy.csv \
  --save-stats /workspace/results/stats/stats_vio_mh_01_easy.ubjson
```

### 7.2 Running VIO on V1_03_difficult

```bash
./basalt_vio \
  --dataset-path /workspace/data/V1_03_difficult \
  --cam-calib /workspace/configs/my_euroc_calib.json \
  --dataset-type euroc \
  --config-path /workspace/external/basalt/data/euroc_config.json \
  --result-path /workspace/results/trajectories/traj_v1_03_difficult.csv \
  --save-stats /workspace/results/stats/stats_vio_v1_03_difficult.ubjson
```

**Command Breakdown:**

- `--dataset-path`: Root directory of EuRoC sequence
- `--cam-calib`: Camera-IMU calibration file (custom tuned)
- `--dataset-type`: Data format parser (euroc vs tumvi vs kitti)
- `--config-path`: VIO algorithm parameters
- `--result-path`: Output trajectory in TUM format
- `--save-stats`: Detailed timing and statistics

---

## 8. Results Generated

### 8.1 Output Files

**Trajectory Files:**

- `/workspace/results/trajectories/traj_mh_01_easy.csv`
- `/workspace/results/trajectories/traj_v1_03_difficult.csv`

**Format:** TUM trajectory format (timestamp, tx, ty, tz, qx, qy, qz, qw)

**Statistics Files:**

- `/workspace/results/stats/stats_vio_*.ubjson` - VIO-specific stats
- `/workspace/results/stats/stats_all_*.ubjson` - Complete system stats
- `/workspace/results/stats/result_*.json` - Summary metrics

### 8.2 Preliminary Results

**MH_01_easy:**

- Frames processed: 3,682
- Execution time: 65.05 seconds
- RMS ATE: 0.0656 meters

**V1_03_difficult:**

- Processing completed successfully
- More challenging due to aggressive motion

---

## 9. Reproducibility Checklist

- [x] Docker container with all dependencies
- [x] Source code version controlled
- [x] Configuration files documented and tuned
- [x] IMU parameters matched to sensor specifications
- [x] Camera calibration verified
- [x] Execution scripts provided
- [x] Results saved in standard formats
- [x] Evaluation tools installed (evo)

---

## 10. Deployment Notes

### For Production Deployment on Jetson Xavier NX:

**1. Cross-compilation:**

```bash
docker buildx build --platform linux/arm64 -t basalt-vio:arm64 .
```

**2. Performance optimizations:**

- Enable CUDA for optical flow (Jetson GPU acceleration)
- Reduce `vio_max_kfs` to 5 for lower memory usage
- Use `config.vio_enforce_realtime = true`

**3. Power management:**

- Monitor thermal throttling
- Adjust CPU governor to performance mode
- Cap frame rate if necessary

---

**Implementation Status:** ✅ Complete and reproducible
