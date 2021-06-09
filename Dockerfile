FROM python:3.8-slim-buster
WORKDIR sequencer
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY bgp bgp
