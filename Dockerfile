FROM python:3.8-slim-buster
RUN apt-get update && apt-get install -y git
RUN git https://github.com/Open-Book-Genome-Project/sequencer/ sequencer
WORKDIR sequencer
RUN mkdir results
RUN pip3 install -r requirements.txt