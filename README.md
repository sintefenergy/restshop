# REST SHOP

REST SHOP is built on [FastAPI](https://fastapi.tiangolo.com/). Hosting of the server with uvicorn or docker is explained below, for other hosting options please visit the [FastAPI documentation](https://fastapi.tiangolo.com/deployment/).

> WARNING: REST SHOP does not implement secure communication and should never be exposed on the internet.

## Start REST SHOP server with uvicorn on Windows

REST SHOP requires pyshop. Please visit the [pyshop GitHub repo](https://github.com/sintef-energy/pyshop) for installation guidelines.

Make sure [uvicorn](https://www.uvicorn.org/) is installed. Clone this repository and navigate to root with Command Prompt or PowerShell. Make sure all requirements are installed in Python with:
```
pip install -r requirements.txt
```

To start the server, run the following commnad:
```
uvicorn main:app --host 127.0.0.1 --port 8000
```

## Run tests

Make sure test requirements are installed:
```
pip install -r requirements-test.txt
```

Run all tests:
```
pytest
```

## Build dockerimage

The restshop image requires SHOP binary files. Put the required files specified in [readme.txt](https://github.com/sintef-energy/restshop/blob/main/binaries/readme.txt) in the binaries folder.

Navigate to the root of this repository and run

```
docker build -t restshop .
```

## Start restshop server

```
docker run --rm --name restshop -p 8000:8000 restshop
```

## Check the swagger documentation

Open your favorite browser and visit

http://localhost:8000/docs

## Run the basic example

This step requires you to have a python environment with the following packages

- requests
- pandas
- numpy
- matplotlib

Then run the basic example at the root of this repo.

```
python basic.py
```

## Debugging

Each SHOP session is running a separate instance of SHOP. By setting the "log_file" attribute when creating sessions, SHOP generates a python-log that enables recreating a workflow. The log file is saved inside the docker container, but can be copied to the current of your local file system using the following command:
```
docker cp {container id}:/root/restshop/{logfile} .
```

Running docker container can be listed with the command:
```
docker ps
```

## Export image

Docker images can be compressed and exported for external users using the following command where the .tar.gz is a compressed image file and restshop is the name of the image to export:
```
docker image save -o restshop.tar.gz restshop
```