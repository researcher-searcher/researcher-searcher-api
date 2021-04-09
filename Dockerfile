FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

COPY ./requirements.txt /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

#RUN python -m spacy download en_core_web_lg
RUN pip install spacy-universal-sentence-encoder
#RUN pip install pydantic==0.18.2

#RUN pip install https://github.com/MartinoMensio/spacy-universal-sentence-encoder/releases/download/v0.4.0/en_use_lg-0.4.0.tar.gz#en_use_lg-0.4.0
