# REST SHOP

REST SHOP is built as a container service using docker. On windows you will need to install docker desktop, it is recommended that you use the wsl 2 backend. Installation instructions can be found here -> [docker-for-windows]("https://docs.docker.com/docker-for-windows/install/").

Building restshop is a two stage process, since the rest/python layer is made open, whilst the backend, the shop-core, is closed. The first step is to build the SHOP core image.

## 1. Building SHOP

> NOTE: If you already have an image of the shop core locally, you can skip this stage. It is important that the local image is called shop.

In order to build, you will need a local copy of the svn repository of shop. You need it checked out to a branch that supports the logging callback and pyshop in general.

Navigate to the directory of the svn repository, and copy paste the file dockerfiles/shop/Dockerfile into the root of this repo.

Now you may proceed to build the shop image (assuming you're standing in the root of the svn repo where you just placed the Dockerfile).

```
docker build -t shop .
```

## 2. Build restshop

The restshop image is based on the shop image. Make sure you have built this first.

Navigate to the root of this repository, and then

```
docker build -t restshop .
```

## 3. Start restshop server

```
docker run --rm --name restshop -p 8000:8000 restshop
```

## 4. Check the swagger documentation

Open your favorite browser and visit

http://localhost:8000/docs

## 5. Run the basic example

This step requires you to have a python environment with the following packages

- requests
- pandas
- numpy
- matplotlib

Then run the basic example at the root of this repo.

```
python basic.py
```

## 6. Debugging

Each SHOP session is running a separate instance of SHOP. By setting the "log_file" attribute when creating sessions, SHOP generates a python-log that enables recreating a workflow. The log file is saved inside the docker container, but can be copied to the current of your local file system using the following command:
```
docker cp {container id}:/root/restshop/{logfile} .
```

Running docker container can be listed with the command:
```
docker ps
```

## 7. Export image

Docker images can be compressed and exported for external users using the following command where the .tar.gz is a compressed image file and restshop is the name of the image to export:
```
docker image save -o restshop.tar.gz restshop
```
