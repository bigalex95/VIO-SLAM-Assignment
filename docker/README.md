# Docker Setup for VIO-SLAM Assignment

This directory contains Docker configurations for the VIO-SLAM assignment.

## Files

- **Dockerfile.dev** - Development environment with interactive shell
- **Dockerfile** - Production environment that runs the full pipeline automatically
- **docker-compose.yml** - Orchestrates both containers

## Quick Start

### Option 1: Development Container (Interactive)

For development and debugging:

```bash
# Build and run
cd docker
docker-compose up -d dev
docker-compose exec dev bash

# Or build directly
docker build -f Dockerfile.dev -t vio-slam-dev ..
docker run -it -v $(pwd)/..:/workspace vio-slam-dev

# Inside container, run manually:
cd /workspace/external/basalt
cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build

# Run tests
/workspace/scripts/run_vio_tests.sh

# Run evaluation
/workspace/scripts/evaluate_results.sh
```

### Option 2: Production Container (Automated)

For automated execution of the entire pipeline:

```bash
# Build and run the full pipeline
cd docker
docker-compose up run

# Or build directly
docker build -f Dockerfile -t vio-slam-run ..
docker run -v $(pwd)/../data:/workspace/data \
           -v $(pwd)/../results:/workspace/results \
           vio-slam-run
```

The production container will automatically:

1. ✅ Clone and build Basalt (if not present)
2. ✅ Run VIO tests on both datasets
3. ✅ Generate trajectories
4. ✅ Evaluate results with evo
5. ✅ Create plots and statistics

## What Each Dockerfile Does

### Dockerfile.dev (Development)

- Installs all system dependencies
- Builds Pangolin for GUI visualization
- Installs evo for trajectory evaluation
- **Does NOT** build Basalt automatically
- Provides interactive bash shell for development
- Ideal for: debugging, testing, GUI visualization

### Dockerfile (Production)

- Everything from Dockerfile.dev, plus:
- Clones Basalt repository (if needed)
- Builds Basalt automatically
- Copies project files into container
- Runs automated pipeline on startup:
  - VIO tests (`run_vio_tests.sh`)
  - Evaluation (`evaluate_results.sh`)
- Exits after completion
- Ideal for: CI/CD, batch processing, automated testing

## Volume Mounts

Both containers expect these volumes:

```yaml
volumes:
  - ../data:/workspace/data # EuRoC datasets
  - ../results:/workspace/results # Output trajectories and plots
```

## Data Requirements

Before running, ensure you have the EuRoC datasets:

```
data/
├── MH_01_easy/
│   └── mav0/
└── V1_03_difficult/
    └── mav0/
```

Download using:

```bash
# From host machine
./scripts/download_euroc.sh
```

## Output Structure

After running the production container:

```
results/
├── trajectories/
│   ├── traj_mh_01_easy.csv
│   └── traj_v1_03_difficult.csv
├── stats/
│   ├── stats_vio_mh_01_easy.ubjson
│   └── stats_vio_v1_03_difficult.ubjson
├── plots/
│   ├── mh_01_easy_ate.png
│   └── v1_03_difficult_ate.png
└── evaluation/
    ├── mh_01_easy/
    └── v1_03_difficult/
```

## Environment Variables

### Production Container

- `KEEP_RUNNING=true` - Keep container running after pipeline completes (for debugging)
- `MPLBACKEND=Agg` - Use non-interactive matplotlib backend (headless mode)

Example:

```bash
docker run -e KEEP_RUNNING=true \
           -v $(pwd)/../data:/workspace/data \
           -v $(pwd)/../results:/workspace/results \
           vio-slam-run
```

## Troubleshooting

### GUI Not Working in Dev Container

Make sure X11 forwarding is enabled:

```bash
xhost +local:docker
docker run -it \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $(pwd)/..:/workspace \
    vio-slam-dev
```

### Build Fails

Check you have enough disk space and RAM:

- Disk: ~5GB required
- RAM: 4GB minimum, 8GB recommended

### Tests Fail

Ensure datasets are properly mounted and have correct structure:

```bash
docker run -v $(pwd)/../data:/workspace/data vio-slam-run ls -la /workspace/data
```

## CI/CD Integration

Use the production Dockerfile in your CI pipeline:

```yaml
# Example GitLab CI
test:
  image: docker:latest
  services:
    - docker:dind
  script:
    - cd docker
    - docker build -f Dockerfile -t vio-slam-run ..
    - docker run -v $CI_PROJECT_DIR/data:/workspace/data \
      -v $CI_PROJECT_DIR/results:/workspace/results \
      vio-slam-run
  artifacts:
    paths:
      - results/
```

## Performance Notes

- **Dev container**: Interactive, minimal startup time
- **Production container**: Full build + execution ~15-30 minutes (depending on hardware)
- Basalt build time: ~5-10 minutes
- VIO tests: ~5-10 minutes per dataset
- Evaluation: ~1-2 minutes

## License

See [LICENSE](../LICENSE) file in project root.
