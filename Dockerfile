FROM shop/linux/python3.8/core:latest as core

FROM python:3.8-slim as app

WORKDIR /root/restshop
COPY . .

RUN apt-get update && apt-get install -y git

RUN pip install --upgrade pip &&\
	pip install -r requirements.txt &&\
	pip install git+https://github.com/sintef-energy/pyshop

# Copy in binaries
# RUN cp /root/restshop/binaries/libcplex2010.so /usr/local/lib
COPY --from=core /root/shop_binaries ./binaries/

ENV ICC_COMMAND_PATH=/root/restshop/binaries

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]