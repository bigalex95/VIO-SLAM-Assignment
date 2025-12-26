#!/bin/bash
#
# BASALT VIO Evaluation Script - Phase C (CORRECTED)
#
# Usage: ./scripts/evaluate_results.sh
#

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DATA_DIR="/workspace/data"
RESULTS_DIR="/workspace/results"
PLOTS_DIR="${RESULTS_DIR}/plots"
STATS_DIR="${RESULTS_DIR}/stats"

# Ensure output directories exist
mkdir -p "${PLOTS_DIR}"
mkdir -p "${STATS_DIR}"

# Force matplotlib to use a non-interactive backend (Headless mode)
export MPLBACKEND=Agg

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}BASALT VIO - Phase C Quantitative Evaluation${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to evaluate a specific sequence
evaluate_sequence() {
    local SEQUENCE_NAME=$1
    local GT_PATH=$2
    
    # Define paths
    local TRAJ_FILE="${RESULTS_DIR}/trajectories/traj_${SEQUENCE_NAME}.csv"
    local ATE_PLOT="${PLOTS_DIR}/${SEQUENCE_NAME}_ate.png"
    local RPE_PLOT="${PLOTS_DIR}/${SEQUENCE_NAME}_rpe.png"
    local ATE_ZIP="${STATS_DIR}/${SEQUENCE_NAME}_ate.zip"
    local RPE_ZIP="${STATS_DIR}/${SEQUENCE_NAME}_rpe.zip"

    echo -e "${YELLOW}----------------------------------------${NC}"
    echo -e "${YELLOW}Evaluating: ${SEQUENCE_NAME}${NC}"
    echo -e "${YELLOW}----------------------------------------${NC}"

    # 1. Check if trajectory file exists
    if [ ! -f "${TRAJ_FILE}" ]; then
        echo -e "${RED}Error: Trajectory file not found: ${TRAJ_FILE}${NC}"
        echo "Please run 'run_vio_tests.sh' first."
        return 1
    fi

    # 2. Check if Ground Truth exists
    if [ ! -f "${GT_PATH}" ]; then
        echo -e "${RED}Error: Ground Truth not found: ${GT_PATH}${NC}"
        return 1
    fi

    echo -e "${BLUE}[1/2] Calculating Absolute Trajectory Error (ATE - RMSE)...${NC}"
    
    # Remove previous results to avoid overwrite prompts
    rm -f "${ATE_PLOT}" "${ATE_ZIP}" "${STATS_DIR}/${SEQUENCE_NAME}_ate_report.txt"
    rm -f "${PLOTS_DIR}/${SEQUENCE_NAME}_ate"*.png

    # Run EVO APE (Absolute Pose Error)
    # REMOVED --no_show, ADDED --save_plot which usually suppresses window in Agg mode
    evo_ape euroc "${GT_PATH}" "${TRAJ_FILE}" \
        --align \
        --plot_mode xyz \
        --save_plot "${ATE_PLOT}" \
        --save_results "${ATE_ZIP}" > "${STATS_DIR}/${SEQUENCE_NAME}_ate_report.txt"
    
    # Extract RMSE from the report for quick display
    RMSE=$(grep "rmse" "${STATS_DIR}/${SEQUENCE_NAME}_ate_report.txt" | awk '{print $2}')
    echo -e "      ATE RMSE: ${GREEN}${RMSE} m${NC}"
    echo -e "      Plot saved to: ${ATE_PLOT}"

    echo ""
    echo -e "${BLUE}[2/2] Calculating Relative Pose Error (RPE - Drift)...${NC}"

    # Remove previous results to avoid overwrite prompts
    rm -f "${RPE_PLOT}" "${RPE_ZIP}" "${STATS_DIR}/${SEQUENCE_NAME}_rpe_report.txt"
    rm -f "${PLOTS_DIR}/${SEQUENCE_NAME}_rpe"*.png

    # Run EVO RPE (Relative Pose Error)
    evo_rpe euroc "${GT_PATH}" "${TRAJ_FILE}" \
        --align \
        --delta 1 --delta_unit m \
        --plot_mode xyz \
        --save_plot "${RPE_PLOT}" \
        --save_results "${RPE_ZIP}" > "${STATS_DIR}/${SEQUENCE_NAME}_rpe_report.txt"

    # Extract RMSE from the report
    RPE_RMSE=$(grep "rmse" "${STATS_DIR}/${SEQUENCE_NAME}_rpe_report.txt" | awk '{print $2}')
    echo -e "      RPE RMSE: ${GREEN}${RPE_RMSE} m${NC}"
    echo -e "      Plot saved to: ${RPE_PLOT}"
    
    return 0
}

# --- Main Execution ---

# 1. Evaluate MH_01_easy
evaluate_sequence "mh_01_easy" \
    "${DATA_DIR}/MH_01_easy/mav0/state_groundtruth_estimate0/data.csv"

echo ""

# 2. Evaluate V1_03_difficult
evaluate_sequence "v1_03_difficult" \
    "${DATA_DIR}/V1_03_difficult/mav0/state_groundtruth_estimate0/data.csv"


echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Evaluation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Summary:"
echo "1. MH_01_easy:"
echo "   - Report: ${STATS_DIR}/mh_01_easy_ate_report.txt"
echo "   - Plot:   ${PLOTS_DIR}/mh_01_easy_ate.png"
echo ""
echo "2. V1_03_difficult:"
echo "   - Report: ${STATS_DIR}/v1_03_difficult_ate_report.txt"
echo "   - Plot:   ${PLOTS_DIR}/v1_03_difficult_ate.png"
echo ""