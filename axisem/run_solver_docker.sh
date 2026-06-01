#!/usr/bin/env bash
# Run ./submit.csh <RUN_NAME> from the SOLVER directory inside Docker.
# Keeps the container alive until all axisem MPI processes finish.
#
# Usage:  ./run_solver_docker.sh [RUN_NAME]
# Default RUN_NAME: MARS
#
# Example:
#   ./run_solver_docker.sh MARS

set -e

RUN_NAME="${1:-MARS}"
AXISEM_ROOT="$(cd "$(dirname "$0")" && pwd)"
SOLVER_DIR="$AXISEM_ROOT/SOLVER"
PROJECT_ROOT="$(dirname "$AXISEM_ROOT")"
IMAGE="axisem-solver-runtime"

# Build the image once; skip if it already exists
if ! docker image inspect "$IMAGE" > /dev/null 2>&1; then
    echo "Building Docker runtime image (one-time)..."
    docker build -f "$AXISEM_ROOT/Dockerfile.solver" -t "$IMAGE" "$AXISEM_ROOT"
fi

echo "Running: ./submit.csh $RUN_NAME  (inside Docker, SOLVER dir)"

# Mount the whole project root at the same absolute path so that:
#   - ../make_axisem.macros resolves correctly from SOLVER/
#   - MESHES/ symlinks and mesh_params.h are accessible
#   - output run directory is written back to the host
# After submit.csh exits the axisem MPI jobs run in the background;
# the loop below keeps the container alive until they finish.
docker run --rm \
    --volume "$PROJECT_ROOT:$PROJECT_ROOT" \
    --workdir "$SOLVER_DIR" \
    "$IMAGE" \
    bash -c "
        csh ./submit.csh $RUN_NAME
        echo 'submit.csh finished — waiting for axisem MPI processes...'
        while pgrep -x axisem > /dev/null 2>&1; do
            sleep 15
        done
        echo 'All axisem processes finished. Results are in SOLVER/$RUN_NAME/'
    "
