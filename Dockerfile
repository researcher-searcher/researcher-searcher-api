FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

COPY ./requirements.txt /app

RUN pip install --upgrade pip

# issues with pip install, so added legacy-resolver
RUN pip install -r requirements.txt --use-deprecated=legacy-resolver


