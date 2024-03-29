FROM python:3.10-slim as app

WORKDIR /root/restshop
COPY . .

RUN apt-get update &&\
	pip install --upgrade pip &&\
	pip install -r requirements.txt &&\
	# pip install sintef-pyshop &&\
	cp /root/restshop/binaries/libcplex2010.so /lib

ENV ICC_COMMAND_PATH=/root/restshop/binaries

EXPOSE 8000

CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:8000"]