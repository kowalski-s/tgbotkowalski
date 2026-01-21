# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота
COPY bot/ ./bot/

# Копируем статические файлы (PDF)
COPY static/ ./static/

# Создаем директорию для данных (БД)
RUN mkdir -p /app/data

# Запускаем бота
CMD ["python", "-m", "bot.main"]
