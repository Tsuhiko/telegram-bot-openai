# Використовуємо офіційне зображення Python 3.12 з Docker Hub
FROM python:3.12-slim-bullseye

# Встановлюємо pip, wheel та setuptools
RUN pip3 install -U pip wheel setuptools

# Копіюємо файл залежностей
COPY ./requirements.txt /tmp/requirements.txt

# Встановлюємо залежності
RUN pip3 install -r /tmp/requirements.txt && rm -r /tmp/requirements.txt

# Копіюємо код додатку
COPY . /code
WORKDIR /code

# Робимо порт 80 доступним для зовнішнього світу поза цим контейнером
EXPOSE 80

# Запускаємо telegram-bot-main.py при запуску контейнера
CMD ["python", "telegram-bot-main.py"]
