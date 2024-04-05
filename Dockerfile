FROM python:3.12-slim-bullseye

RUN pip3 install -U pip wheel setuptools

RUN apt-get update && apt-get install -y default-mysql-client

COPY ./requirements.txt /tmp/requirements.txt

RUN pip3 install -r /tmp/requirements.txt && rm -r /tmp/requirements.txt

COPY . /code
WORKDIR /code

CMD ["python", "telegram-bot-main.py"]
