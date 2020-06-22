FROM python:3-slim

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

VOLUME /tumbot-db

ENV TUMBOT_TOKEN ""
ENV TUMBOT_DBPATH "/tumbot-db"

CMD ["python", "-u", "./main.py"]
