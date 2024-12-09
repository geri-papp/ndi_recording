FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG FFMPEG_VERSION=4.1.11

ENV NVIDIA_DRIVER_CAPABILITIES=all

# Install runtime dependencies
RUN apt-get update -qq --fix-missing && \
    apt-get install -y --no-install-recommends \
        git \
        yasm \
        curl \
        wget \
        avahi-daemon \
        libavahi-client3 \
        dbus \
        libblas-dev \
        libnuma1 \
        libnuma-dev \
        libx264-dev \
        libvpx-dev \
        libass-dev \
        libfreetype6-dev \
        libgnutls28-dev \
        libmp3lame-dev \
        libopus-dev \
        libvorbis-dev \
        python3.10 python3.10-venv python3.10-distutils && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Build FFmpeg with NVIDIA GPU support
WORKDIR /tmp/ffmpeg-build
RUN wget -q https://github.com/FFmpeg/nv-codec-headers/releases/download/n11.0.10.3/nv-codec-headers-11.0.10.3.tar.gz && \
    tar -xzf nv-codec-headers-11.0.10.3.tar.gz && \
    cd nv-codec-headers-11.0.10.3 && \
    make install && \
    cd .. && rm -rf nv-codec-headers-11.0.10.3*

RUN wget -q https://ffmpeg.org/releases/ffmpeg-${FFMPEG_VERSION}.tar.gz && \
    tar -xzf ffmpeg-${FFMPEG_VERSION}.tar.gz && \
    cd ffmpeg-${FFMPEG_VERSION} && \
    ./configure \
        --enable-nonfree \
        --enable-cuda \
        --enable-nvenc \
        --enable-cuvid \
        --enable-libnpp \
        --prefix=/usr/local \
        --pkg-config-flags="--static" \
        --extra-cflags=-I/usr/local/cuda/include \
        --extra-ldflags=-L/usr/local/cuda/lib64 \
        --extra-libs="-lpthread -lm" \
        --bindir="/usr/local/bin" \
        --disable-static \
        --enable-shared && \
    make -j$(nproc) && make install && \
    cd .. && rm -rf ffmpeg-${FFMPEG_VERSION}*

# Set Python 3.10 as the default python version
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 && \
    update-alternatives --set python3 /usr/bin/python3.10

# Copy application code
WORKDIR /app
COPY main.py /app/
COPY requirements/prod.txt /app/
COPY src/ /app/src
COPY rtdetrv2.onnx /app/

# Install Python dependencies in a virtual environment
RUN python3 -m venv .venv && \
    ./.venv/bin/pip install --no-cache-dir -r prod.txt

# Final cleanup
# RUN apt-get remove -y git wget yasm && \
#     apt-get autoremove -y && \
#     apt-get clean && \
#     rm -rf /tmp/* /root/.cache

CMD ["/bin/bash", "-c", "source /app/.venv/bin/activate && exec bash"]
