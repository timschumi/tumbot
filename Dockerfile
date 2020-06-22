FROM python:3-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd tumbot && useradd --no-log-init -g tumbot tumbot
RUN mkdir -p /tumbot-db && chown -R tumbot:tumbot /tumbot-db
VOLUME /tumbot-db

COPY . .

USER tumbot

ENV TUMBOT_TOKEN ""
ENV TUMBOT_DBPATH "/tumbot-db"

CMD ["python", "-u", "./main.py"]
