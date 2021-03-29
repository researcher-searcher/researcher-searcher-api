FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

COPY ./requirements.txt /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
