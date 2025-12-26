# Phase D: Engineering Improvement Proposal

## 1. Problem Identification: Long-term Drift & Loop Closure

### Observation
While the current Basalt VIO implementation demonstrates excellent local tracking accuracy (ATE < 10cm on EuRoC datasets), it is fundamentally an odometry system. Like all dead-reckoning systems, it accumulates drift over time (unbounded error).

**Current Limitations:**
1. **No Loop Closure:** When the drone revisits a previously mapped area, the system does not recognize it. It creates a new, duplicate map section instead of correcting the accumulated drift.
2. **No Global Consistency:** The estimated trajectory is locally smooth but globally inconsistent over long durations (> 10-20 minutes).
3. **Relocalization Failure:** If tracking is lost (e.g., due to aggressive motion or lighting change), the system cannot recover its pose relative to the previous map; it must restart a new trajectory.

### Impact
For a drone operating in a warehouse or tunnel for extended periods, this drift (approx. 2-4% of distance traveled) will eventually cause the estimated position to diverge significantly from reality, making autonomous navigation and landing unsafe.

---

## 2. Proposed Solution: Bag-of-Words (BoW) Loop Closure

I propose integrating a **Visual Loop Closure** module based on the **DBoW2** or **FBOW** (Fast Bag of Words) library. This is a standard approach used in systems like ORB-SLAM3 and VINS-Mono but is currently absent in the core Basalt VIO pipeline.

### Technical Architecture

#### A. Keyframe Database
- **Selection:** Maintain a database of "Keyframes" (selected every ~0.5 seconds or based on parallax).
- **Description:** For each keyframe, compute binary descriptors (e.g., ORB or BRIEF) for the tracked features.
- **Storage:** Store these descriptors in an inverted index structure for O(1) retrieval.

#### B. Place Recognition (Loop Detection)
- **Query:** For every new keyframe, query the database for similar images.
- **Scoring:** Calculate a similarity score based on shared "visual words" (clusters of descriptors).
- **Verification:**
    1. **Geometric Verification:** If a candidate match is found, perform a RANSAC-based PnP (Perspective-n-Point) check to ensure the geometric structure matches.
    2. **Temporal Consistency:** Require consecutive frames to match the same loop candidate to reject false positives.

#### C. Pose Graph Optimization (PGO)
- **Constraint Generation:** When a loop is verified, calculate the relative pose transformation ($T_{loop}$) between the current frame and the matched past frame.
- **Optimization:** Add this constraint to a global **Pose Graph**.
    - Nodes: Keyframe poses.
    - Edges: VIO relative motion factors (sequential) and Loop Closure factors (non-sequential).
- **Solver:** Run a background optimization (using g2o or Ceres) to distribute the drift error across the entire trajectory, snapping the start and end points together.

---

## 3. Implementation Plan

### Step 1: Descriptor Integration
- **Task:** Modify the Basalt frontend to compute ORB descriptors for the existing optical flow patches.
- **Challenge:** Basalt uses optical flow on raw pixels; ORB requires oriented FAST corners. We may need to compute descriptors only for Keyframes to save compute.

### Step 2: Loop Detection Module
- **Library:** Use **FBOW** (highly optimized version of DBoW2).
- **Integration:** Create a separate thread `LoopClosureThread` that receives Keyframes from the VIO backend.
- **Action:** Build the vocabulary database online or load a pre-trained one (e.g., trained on COCO or similar environments).

### Step 3: Global Pose Graph
- **Library:** Use **g2o** or **Ceres Solver**.
- **Integration:**
    - When VIO marginalizes a frame, add it to the Pose Graph.
    - When a loop is detected, add a "Loop Edge".
    - Run optimization in a low-priority background thread.
- **Feedback:** Correct the current VIO state drift based on the PGO result (4-DOF pose correction).

---

## 4. Expected Improvements

| Metric | Current System (VIO Only) | Proposed System (VIO + Loop Closure) |
| :--- | :--- | :--- |
| **Drift** | Unbounded (grows with time) | Bounded (resets upon loop closure) |
| **Long-term Accuracy** | ~1-3% of distance | < 0.5% of distance |
| **Relocalization** | Not supported | Supported (can recover lost track) |
| **Map Consistency** | Duplicate corridors/rooms | Single, consistent global map |
| **Compute Load** | Low (1 core) | Medium (1 core + 1 background thread) |

### Feasibility on Embedded Hardware (Jetson)
- **Memory:** The BoW vocabulary (~150MB) and Keyframe database will increase RAM usage.
- **Compute:** Loop detection is fast (~5-10ms). Pose Graph Optimization is heavy but runs infrequently (every few seconds) and in the background, so it will not block the high-frequency VIO control loop (20-30Hz).

---

## 5. Conclusion

Integrating a BoW-based loop closure system is the most logical next step to transform this VIO odometry pipeline into a full SLAM system capable of long-endurance autonomous missions. It addresses the critical issue of drift without requiring expensive new sensors (like LiDAR).
