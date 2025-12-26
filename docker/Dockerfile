FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# 1. Install System Dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    unzip \
    libtbb-dev \
    libboost-all-dev \
    libeigen3-dev \
    libopencv-dev \
    libfmt-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    libglew-dev \
    libpng-dev \
    libjpeg-dev \
    libjson-glib-dev \
    libx11-dev \
    libxext-dev \
    libxcomposite-dev \
    libxcursor-dev \
    libxinerama-dev \
    libxi-dev \
    libxrandr-dev \
    libxrender-dev \
    libepoxy-dev \
    python3-pip \
    python3-dev \
    python3-tk \
    ninja-build \
    gdb \
    ca-certificates \
    libssl-dev \
    libbz2-dev \
    liblz4-dev \
    && rm -rf /var/lib/apt/lists/*

# 1.5. Install CMake 3.27+ (Basalt requires 3.24+, Ubuntu 22.04 has 3.22)
RUN wget https://github.com/Kitware/CMake/releases/download/v3.27.9/cmake-3.27.9-linux-x86_64.sh -O /tmp/cmake.sh && \
    chmod +x /tmp/cmake.sh && \
    /tmp/cmake.sh --prefix=/usr/local --skip-license && \
    rm /tmp/cmake.sh

# 2. Build Pangolin from Source (Required for GUI)
WORKDIR /tmp
RUN git clone --recursive https://github.com/stevenlovegrove/Pangolin.git
WORKDIR /tmp/Pangolin
RUN cmake -B build -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DBUILD_PANGOLIN_GUI=ON \
    -DBUILD_PANGOLIN_VARS=ON \
    -DBUILD_EXAMPLES=OFF \
    -DBUILD_TESTS=OFF \
    && cmake --build build \
    && cmake --install build \
    && cd /tmp && rm -rf Pangolin

# 3. Install Evo for evaluation
RUN pip3 install evo --upgrade --no-binary evo

# 4. Clone and Build Basalt FIRST (for better caching)
WORKDIR /workspace
RUN mkdir -p /workspace/external && \
    git clone --recursive https://gitlab.com/VladyslavUsenko/basalt.git /workspace/external/basalt

WORKDIR /workspace/external/basalt
RUN cmake -B build \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    && cmake --build build -j8

# 5. Install Python dependencies (cached unless requirements.txt changes)
WORKDIR /workspace
COPY requirements.txt /workspace/
RUN pip3 install -r requirements.txt

# 6. Copy project files (these change frequently, so keep at end)
COPY configs/ /workspace/configs/
COPY scripts/ /workspace/scripts/
COPY docs/ /workspace/docs/
COPY README.md LICENSE /workspace/

# 7. Make scripts executable
RUN chmod +x /workspace/scripts/*.sh

# 8. Create entrypoint script
RUN echo '#!/bin/bash\n\
    set -e\n\
    \n\
    echo "========================================"\n\
    echo "VIO-SLAM Assignment - Automated Pipeline"\n\
    echo "========================================"\n\
    echo ""\n\
    \n\
    # Check if data exists, if not download it\n\
    if [ ! -d "/workspace/data/MH_01_easy" ] || [ ! -d "/workspace/data/V1_03_difficult" ]; then\n\
    echo "Dataset not found. Please mount the data directory or download manually."\n\
    echo "Expected data structure:"\n\
    echo "  /workspace/data/MH_01_easy/"\n\
    echo "  /workspace/data/V1_03_difficult/"\n\
    echo ""\n\
    echo "Skipping data download..."\n\
    fi\n\
    \n\
    # Run VIO tests\n\
    echo ""\n\
    echo "Step 1: Running VIO tests..."\n\
    echo "========================================"\n\
    if [ -f "/workspace/scripts/run_vio_tests.sh" ]; then\n\
    /workspace/scripts/run_vio_tests.sh\n\
    echo "✅ VIO tests completed"\n\
    else\n\
    echo "⚠️  VIO test script not found, skipping..."\n\
    fi\n\
    \n\
    # Run evaluation\n\
    echo ""\n\
    echo "Step 2: Evaluating results (basic evo)..."\n\
    echo "========================================"\n\
    if [ -f "/workspace/scripts/evaluate_results.sh" ]; then\n\
    /workspace/scripts/evaluate_results.sh\n\
    echo "✅ Basic evaluation completed"\n\
    else\n\
    echo "⚠️  Basic evaluation script not found, skipping..."\n\
    fi\n\
    \n\
    # Run detailed Python evaluation\n\
    echo ""\n\
    echo "Step 3: Running detailed evaluation (Python)..."\n\
    echo "========================================"\n\
    if [ -f "/workspace/scripts/evaluate_trajectories.py" ]; then\n\
    python3 /workspace/scripts/evaluate_trajectories.py --dataset all\n\
    echo "✅ Detailed evaluation completed"\n\
    else\n\
    echo "⚠️  Python evaluation script not found, skipping..."\n\
    fi\n\
    \n\
    # Summary\n\
    echo ""\n\
    echo "========================================"\n\
    echo "Pipeline completed successfully!"\n\
    echo "========================================"\n\
    echo ""\n\
    echo "Results available at:"\n\
    echo "  - Trajectories: /workspace/results/trajectories/"\n\
    echo "  - Statistics: /workspace/results/stats/"\n\
    echo "  - Plots: /workspace/results/plots/"\n\
    echo "  - Evaluation: /workspace/results/evaluation/"\n\
    echo ""\n\
    \n\
    # Keep container running if requested\n\
    if [ "$KEEP_RUNNING" = "true" ]; then\n\
    echo "Keeping container running..."\n\
    tail -f /dev/null\n\
    fi\n\
    ' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
