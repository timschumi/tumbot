FROM docker.io/python:3

RUN groupadd dbot && useradd --no-log-init -g dbot dbot
RUN mkdir -p /dbot-db && chown -R dbot:dbot /dbot-db
VOLUME /dbot-db

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER dbot

ENV DBOT_TOKEN ""
ENV DBOT_DBPATH "/dbot-db"

CMD ["python", "-u", "./main.py"]
