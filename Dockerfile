# Використовуємо офіційне зображення Python 3.12 з Docker Hub
FROM python:3.12-slim-bullseye

# Встановлюємо робочу директорію в контейнері
WORKDIR /app

# Копіюємо вміст поточної директорії в контейнер у /app
ADD . /app

# Встановлюємо необхідні пакети, зазначені у requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Робимо порт 80 доступним для зовнішнього світу поза цим контейнером
EXPOSE 80

# Запускаємо telegram-bot-main.py при запуску контейнера
CMD ["python", "telegram-bot-main.py"]
