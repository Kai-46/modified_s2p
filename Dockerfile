# @kai
FROM ubuntu:18.04

LABEL maintainer="Carlo de Franchis <carlodef@gmail.com>"

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y apt-utils
RUN apt-get update && apt-get install -y \
    build-essential \
    geographiclib-tools \
    git \
    libfftw3-dev \
    libgdal-dev \
    libgeographic-dev \
    libgeotiff-dev \
    libtiff5-dev \
    python \
    python-numpy \
    python-pip \
    cmake \
    software-properties-common \
    dialog

RUN pip install -U pip
RUN pip install utm bs4 lxml requests

# install GDAL
RUN apt-get update && apt-get install -y gdal-bin python-gdal

# install PDAL
RUN apt-get update && apt-get install -y pdal python-pdal

# Install s2p from MISS3D/s2p
# RUN git clone https://github.com/MISS3D/s2p.git --recursive
# RUN cd s2p && make all

# build image from the current directory
WORKDIR /s2p
ADD . /s2p
RUN make -j4 all