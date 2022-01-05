FROM python:3.8-rc-slim as base

# to avoid getting prompted for user input (specifying timezone)
ENV DEBIAN_FRONTEND=noninteractive

RUN apt update
RUN apt-get -y install cmake
RUN apt-get -y install build-essential
RUN apt-get -y install python3
RUN apt-get -y install python3-pip
RUN pip3 install pybind11

# ENV SHOP_PYTHON=/usr/local/lib/python3.8/dist-packages/pybind11/include
# ENV PYTHON_INCLUDE=/usr/include/python3.8

ENV SHOP_PYTHON=/usr/local/lib/python3.8/site-packages/pybind11/include
ENV PYTHON_INCLUDE=/usr/local/include/python3.8

WORKDIR /root
COPY ./shop shop

RUN apt-get -y install libgtest-dev

WORKDIR /root/shop/bin
RUN cmake -DCMAKE_BUILD_TYPE=Release ../src
RUN make

WORKDIR /root
COPY ./SDK SDK

RUN cp /root/shop/bin/*.so /root/SDK/pyshop

# TODO: from here on we could base on an image with only the .so's and python environment?
# FROM python-alpine as app

ENV ICC_COMMAND_PATH=/root/shop/bin

WORKDIR /root/SDK
RUN pip3 install .





