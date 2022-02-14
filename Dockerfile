FROM python:3.8-slim-buster
RUN apt-get update && apt-get install -y git
WORKDIR sequencer
COPY . .
RUN mkdir results
RUN pip3 install -r requirements.txt
