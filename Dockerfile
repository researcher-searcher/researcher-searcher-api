FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

ENV PATH="/root/miniconda3/bin:${PATH}"
ARG PATH="/root/miniconda3/bin:${PATH}"
RUN apt-get update

RUN wget \
    https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh 
RUN conda --version

# Create the environment:
COPY environment.yml .
RUN conda env create -f environment.yml
RUN conda activate researcher-searcher-api

#COPY ./app /app