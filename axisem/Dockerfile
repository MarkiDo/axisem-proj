FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
# Allow OpenMPI to run as root inside the container
ENV OMPI_ALLOW_RUN_AS_ROOT=1
ENV OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1

RUN apt-get update && apt-get install -y \
    gfortran \
    gcc \
    libopenmpi-dev \
    openmpi-bin \
    libnetcdff-dev \
    python3 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir click netcdf4 scipy numpy

WORKDIR /axisem

COPY . .

# Use optimized release build
RUN ./copytemplates.sh release

# Makefile generates gitversion.h from git history; provide a stub when
# the full .git history is not present in the build context
RUN git rev-parse HEAD > /dev/null 2>&1 \
    && make MESHER/gitversion.h SOLVER/gitversion.h \
    || { \
        echo 'character(len=*), parameter :: gitversion = "docker-build"' > MESHER/gitversion.h; \
        echo 'character(len=*), parameter :: gitversion = "docker-build"' > SOLVER/gitversion.h; \
    }

RUN make -j4

# Output directory is expected to be mounted from the host
VOLUME ["/axisem/runs"]

CMD ["/bin/bash"]
