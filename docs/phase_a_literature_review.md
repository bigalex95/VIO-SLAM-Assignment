# Phase A: Literature Review & Method Selection

## 1. State-of-the-Art VIO/SLAM Frameworks Analysis

### Overview

For autonomous drone operations in GPS-denied environments, Visual-Inertial Odometry (VIO) and SLAM systems are critical for robust state estimation. This review examines three leading open-source frameworks published within the last 3-5 years.

---

## 2. Comparative Analysis of Three Leading Frameworks

### 2.1 BASALT (2019-2021)

**Publication:** "Visual-Inertial Mapping with Non-Linear Factor Recovery" (Usenko et al., 2019-2021)

**Architecture:**

- Tightly-coupled visual-inertial optimization
- Non-linear factor recovery for efficient marginalization
- Square-root information filters
- Support for multiple camera models (pinhole, double-sphere, extended unified)

**Computational Efficiency:**

- **Rating: Excellent (9/10)**
- Optimized C++ with TBB parallelization
- Efficient square-root marginalization reduces computation
- **Can run on Jetson platforms:** Yes, with optimization flags
- **Real-time capable:** 30+ FPS on modern hardware
- Memory footprint: ~200-500 MB for typical operation

**Robustness:**

- **Rating: Very Good (8.5/10)**
- Handles low-texture environments reasonably well through optical flow
- Fast motion: Good with proper IMU integration
- Rolling shutter support available
- Challenges: Very aggressive rotations can cause tracking loss

**Loop Closure:**

- **Rating: Limited (6/10)**
- No built-in loop closure detection
- Focuses on VIO odometry rather than full SLAM
- Can be extended with external loop closure modules

**Key Strengths:**

- Clean, modern C++17 codebase
- Excellent documentation and reproducibility
- Strong performance on EuRoC and TUM-VI benchmarks
- Efficient marginalization strategy

**Key Limitations:**

- No semantic understanding
- Limited loop closure capabilities
- Requires good calibration data

---

### 2.2 ORB-SLAM3 (2020-2021)

**Publication:** "ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual-Inertial and Multi-Map SLAM" (Campos et al., 2021)

**Architecture:**

- Feature-based SLAM with ORB descriptors
- Multi-map system for robustness
- Visual-only, Visual-Inertial, and Monocular/Stereo support
- Complete SLAM with relocalization and loop closing

**Computational Efficiency:**

- **Rating: Good (7.5/10)**
- More computationally intensive than BASALT
- **Can run on Jetson platforms:** Yes, but requires optimization
- Feature extraction overhead (ORB computation)
- **Real-time capable:** 20-30 FPS on desktop, 10-20 FPS on Jetson Xavier
- Memory: ~500 MB - 2 GB depending on map size

**Robustness:**

- **Rating: Excellent (9/10)**
- Excellent in low-texture with sufficient features
- Multi-map system recovers from tracking failures
- Fast motion: Very good with IMU integration
- Robust initialization procedures

**Loop Closure:**

- **Rating: Excellent (9.5/10)**
- DBoW2-based place recognition
- Full pose-graph optimization
- Multi-map merging capabilities
- Relocalization after tracking loss

**Key Strengths:**

- Complete SLAM system
- Proven track record (evolution of ORB-SLAM2)
- Excellent loop closure
- Handles multiple sequences

**Key Limitations:**

- Higher computational cost
- Requires sufficient texture for ORB features
- Can fail in completely feature-less environments
- More complex to tune

---

### 2.3 OpenVINS (2019-2021)

**Publication:** "OpenVINS: A Research Platform for Visual-Inertial Estimation" (Geneva et al., 2020)

**Architecture:**

- Filter-based VIO (Extended Kalman Filter - EKF)
- MSCKF (Multi-State Constraint Kalman Filter) implementation
- Modular design for research
- First-estimates Jacobian (FEJ) for consistency

**Computational Efficiency:**

- **Rating: Excellent (9.5/10)**
- Filter-based approach is very efficient
- Lowest computational requirements among the three
- **Can run on Jetson platforms:** Yes, easily (even on Jetson Nano)
- **Real-time capable:** 30+ FPS consistently
- Memory: ~100-300 MB

**Robustness:**

- **Rating: Good (7.5/10)**
- Good performance in nominal conditions
- Fast motion: Good with proper tuning
- Low-texture: Moderate (depends on sufficient features)
- Can be less accurate than optimization-based methods

**Loop Closure:**

- **Rating: Limited (5/10)**
- Basic loop closure support (experimental)
- Primarily focused on odometry
- Not a full SLAM system

**Key Strengths:**

- Extremely efficient
- Easy to deploy on embedded systems
- Modular and extensible
- Good for research and rapid prototyping
- Lower computational overhead

**Key Limitations:**

- Filter-based approach can be less accurate than optimization
- Limited loop closure
- Linearization errors can accumulate
- Less mature than ORB-SLAM3

---

## 3. Comparison Summary Table

| Framework     | VIO Type             | Real-time on Jetson?    | Robustness Notes                              | Loop Closure              |
| :------------ | :------------------- | :---------------------- | :-------------------------------------------- | :------------------------ |
| **BASALT**    | Optimization (Tight) | ✅ Yes (High FPS)       | Excellent in fast motion; good in low texture | ❌ No (Odometry only)     |
| **ORB-SLAM3** | Optimization (Tight) | ⚠️ Yes (Needs tuning)   | Excellent (Multi-map recovery)                | ✅ Yes (Full SLAM)        |
| **OpenVINS**  | Filter (MSCKF)       | ✅ Yes (Very efficient) | Good (Sensitive to linearization)             | ⚠️ Limited (Experimental) |

---

## 4. Method Selection: BASALT

### 4.1 Selection Justification

**For autonomous drone operations in GPS-denied environments, BASALT is selected as the optimal framework for the following technical reasons:**

#### **1. Computational Efficiency for Embedded Deployment**

- BASALT's square-root marginalization and efficient factor graph implementation make it highly suitable for resource-constrained platforms like Nvidia Jetson (common in drone systems)
- Lower memory footprint compared to ORB-SLAM3
- Consistent real-time performance critical for autonomous flight

#### **2. Accuracy in Odometry**

- Optimization-based approach provides superior accuracy compared to filter-based methods (OpenVINS)
- Non-linear factor recovery maintains accuracy while enabling efficient marginalization
- Demonstrated excellent results on EuRoC benchmark (our target dataset)

#### **3. Multi-Camera Support**

- Native support for stereo and multiple camera configurations
- Advanced camera models (double-sphere) better handle wide-angle lenses common in drone platforms
- Better field-of-view coverage critical for confined spaces

#### **4. IMU Integration Quality**

- Tightly-coupled IMU pre-integration
- Handles high-frequency IMU data (typical drones use 200-500 Hz IMU)
- Robust to IMU biases common in MEMS sensors

#### **5. Code Quality and Reproducibility**

- Modern C++17 codebase is maintainable and extensible
- Excellent documentation enables rapid deployment
- Docker-friendly architecture
- Active community support

#### **6. Drone-Specific Advantages**

While ORB-SLAM3's loop closure is appealing, for **first-responder drone missions in warehouses/tunnels**, odometry accuracy is often more critical than loop closure because:

- Missions are typically short-duration (15-30 minutes)
- Paths are often exploration-focused rather than repetitive
- Lower computational overhead leaves headroom for other autonomous functions (planning, obstacle avoidance)
- BASALT's accuracy degrades more gracefully without loop closure

#### **7. Rapid Prototyping and Tuning**

- Clear configuration files make sensor calibration straightforward
- Extensive parameter documentation enables quick tuning
- Good balance between performance and ease of deployment

### 4.2 Drone Platform Suitability

**Target Platform:** DJI Matrice 300 RTK or equivalent with:

- Stereo cameras (752x480 @ 20 Hz)
- BMI088 or similar IMU (200-400 Hz)
- Nvidia Jetson Xavier NX compute module

**Why BASALT fits this platform:**

1. **Power Budget:** BASALT's efficiency leaves thermal and power budget for flight control
2. **Latency:** 30-50ms latency acceptable for 5 m/s flight speeds
3. **Failure Modes:** Graceful degradation without sudden jumps (critical for flight safety)
4. **Sensor Compatibility:** Supports typical drone sensor specifications

### 4.3 Trade-offs Acknowledged

**What we sacrifice by not choosing ORB-SLAM3:**

- No loop closure for long-duration missions
- Cannot relocalize after complete tracking loss
- Less robust in extremely dynamic environments

**Mitigation strategies:**

- Implement external loop closure module if needed (Phase D proposal)
- Use BASALT's robust initialization
- Deploy redundant sensors (downward-facing camera, LiDAR for backup)

### 4.4 Alternative Decision Matrix

If requirements changed:

- **For long-duration mapping missions:** Choose ORB-SLAM3
- **For extremely limited compute (Jetson Nano):** Choose OpenVINS
- **For research/experimentation:** Choose OpenVINS (most modular)

---

## 5. References

1. Usenko, V., Demmel, N., Schubert, D., Stückler, J., & Cremers, D. (2019). "Visual-Inertial Mapping with Non-Linear Factor Recovery." _IEEE Robotics and Automation Letters_.

2. Campos, C., Elvira, R., Rodríguez, J. J. G., Montiel, J. M., & Tardós, J. D. (2021). "ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual-Inertial and Multi-Map SLAM." _IEEE Transactions on Robotics_.

3. Geneva, P., Eckenhoff, K., Lee, W., Yang, Y., & Huang, G. (2020). "OpenVINS: A Research Platform for Visual-Inertial Estimation." _IROS 2020 Workshop_.

4. Burri, M., et al. (2016). "The EuRoC micro aerial vehicle datasets." _International Journal of Robotics Research_.

5. Qin, T., Li, P., & Shen, S. (2018). "VINS-Mono: A Robust and Versatile Monocular Visual-Inertial State Estimator." _IEEE Transactions on Robotics_.

---

**Selection Summary:** BASALT provides the optimal balance of computational efficiency, accuracy, and drone-platform compatibility for GPS-denied autonomous operations, making it the best choice for this assignment and real-world deployment scenarios.
