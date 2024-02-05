FROM python:3.11.1-alpine3.17

WORKDIR /usr/src/app

COPY ../requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .