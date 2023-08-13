# Copyright 2022 Thetaphi Ltd.

# LoraWan Connector application for chirpstack tech stack
# ----------------------------

FROM python:3-slim-buster

# install OS dependencies
RUN apt-get update
RUN apt-get install -y apt-utils
RUN apt-get install -y gcc 

# install python dependencies
COPY ./ ./app/
WORKDIR /app/
RUN pip install -r requirements.txt

# make a directory for logs
RUN mkdir -p ../logs

# build executable
CMD ["python","-u","./chirpstack-connector.py"]
