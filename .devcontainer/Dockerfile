# syntax=docker/dockerfile:1
#
# bufr-monitor dev/CI image.
#
# Adapted from NOAA-EMC/GEODE's Dockerfile: builds gsl-lite, NCEPLIBS-bufr,
# and bufr-query from source on a plain python base, rather than depending
# on an unverified pre-built image
#
# NCEPLIBS_BUFR_REF below (v12.3.0) is close to but not identical to the
# bufr/12.1.0 HPC module Steps 1-2 were validated against on ursa -- worth
# a sanity check on output parity once this image actually runs the
# pipeline, since that's the piece producing your data.

FROM python:3.12
 
ARG USERNAME=developer
ARG GSL_LITE_REF=v1.1.0
ARG NCEPLIBS_BUFR_REF=v12.3.0
ARG BUFR_QUERY_REF=v0.0.5
 
RUN useradd -ms /bin/bash ${USERNAME}
 
# System dependencies required by BUFR tooling.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      ca-certificates \
      cmake \
      curl \
      ecbuild \
      gfortran \
      git \
      libeckit-dev \
      libeigen3-dev \
      libnetcdf-c++4-dev \
      libnetcdf-dev \
      libopenmpi-dev \
      libomp-dev \
      pybind11-dev \
      vim \
      openmpi-bin && \
    rm -rf /var/lib/apt/lists/*
 
# gsl-lite headers
RUN git clone --branch "${GSL_LITE_REF}" --depth 1 \
      https://github.com/gsl-lite/gsl-lite.git /tmp/gsl-lite && \
    cmake -S /tmp/gsl-lite -B /tmp/gsl-lite/build \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX=/usr/local \
      -DGSL_LITE_OPT_BUILD_TESTS=OFF && \
    cmake --install /tmp/gsl-lite/build && \
    rm -rf /tmp/gsl-lite
 
# NCEPLIBS-bufr
RUN git clone --branch "${NCEPLIBS_BUFR_REF}" --depth 1 \
      https://github.com/NOAA-EMC/NCEPLIBS-bufr.git /tmp/NCEPLIBS-bufr && \
    cmake -S /tmp/NCEPLIBS-bufr -B /tmp/NCEPLIBS-bufr/build \
      -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local && \
    cmake --build /tmp/NCEPLIBS-bufr/build -j"$(nproc)" && \
    cmake --install /tmp/NCEPLIBS-bufr/build && \
    rm -rf /tmp/NCEPLIBS-bufr && \
    ldconfig
 
# bufr-query
RUN git clone --branch "${BUFR_QUERY_REF}" --depth 1 \
      https://github.com/NOAA-EMC/bufr-query.git /tmp/bufr-query && \
    mkdir /tmp/bufr-query/build && cd /tmp/bufr-query/build && \
    ecbuild ../ && \
    make -j"$(nproc)" && \
    make install && \
    rm -rf /tmp/bufr-query
 
# Project Python deps. pyproject.toml is expected to declare xarray,
# netCDF4, pandas, matplotlib, cartopy, etc. as normal dependencies.
# emcpy and wxflow are installed separately since neither is on PyPI.
#
# NOTE: if your pyproject.toml's [project] table references a readme
# file (e.g. readme = "README.md"), add a matching
# `COPY README.md /tmp/bufr-monitor/README.md` line below, or the pip
# install will fail looking for a file that isn't in the build context.
COPY pyproject.toml /tmp/bufr-monitor/pyproject.toml
COPY src /tmp/bufr-monitor/src
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir "/tmp/bufr-monitor[dev]" \
      pybind11==3.0.1 \
      scipy \
      scikit-learn \
      cartopy \
      git+https://github.com/NOAA-EMC/wxflow.git \
      git+https://github.com/NOAA-EMC/emcpy.git && \
    rm -rf /tmp/bufr-monitor
 
WORKDIR /home/${USERNAME}
USER ${USERNAME}
 
RUN echo 'alias ls="ls --color=auto"' >> ~/.bashrc && \
    echo 'alias ll="ls -alF --color=auto"' >> ~/.bashrc && \
    echo 'export PS1="\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ "' >> ~/.bashrc && \
    echo 'git config --global --add safe.directory /workspaces/bufr-monitor' >> ~/.bashrc
 
CMD ["/bin/bash"]
