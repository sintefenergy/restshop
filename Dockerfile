FROM shop as base

FROM python:3.8-rc-slim as app

WORKDIR /root/restshop
COPY . .

RUN pip3 install --upgrade pip &&\
	pip install sintef-pyshop &&\
	pip install . &&\
	mkdir /root/binaries

# Copy in binaries from shop base image
COPY --from=base /root/shop_binaries/*.so /root/binaries

# license
#COPY --from=base /root/shop_binaries/SHOP_license.dat /root/binaries

ENV ICC_COMMAND_PATH=/root/binaries

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]