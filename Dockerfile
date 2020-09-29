FROM python:3-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd dbot && useradd --no-log-init -g dbot dbot
RUN mkdir -p /dbot-db && chown -R dbot:dbot /dbot-db
VOLUME /dbot-db

COPY . .

USER dbot

ENV DBOT_TOKEN ""
ENV DBOT_DBPATH "/dbot-db"

CMD ["python", "-u", "./main.py"]
