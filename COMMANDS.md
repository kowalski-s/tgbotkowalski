# Шпаргалка по командам

## Локальная разработка

### Первоначальная настройка
```bash
# Создать виртуальное окружение
python -m venv venv

# Активировать (Windows cmd)
venv\Scripts\activate.bat

# Активировать (Windows PowerShell)
venv\Scripts\Activate.ps1

# Активировать (Linux/Mac)
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Создать .env из примера
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Проверить конфигурацию
python check_config.py
```

### Запуск и остановка
```bash
# Запустить бота
python -m bot.main

# Остановить (в терминале где запущен)
Ctrl+C
```

## Docker (локально)

```bash
# Собрать образ
docker-compose build

# Запустить
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановить
docker-compose down

# Перезапустить
docker-compose restart

# Пересобрать и запустить после изменений
docker-compose up -d --build
```

## Деплой на VPS

### Первоначальная настройка сервера
```bash
# Подключиться по SSH
ssh user@your-server-ip

# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установить Docker Compose
sudo apt install docker-compose -y

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER

# Перелогиниться
exit
```

### Деплой проекта
```bash
# Клонировать репозиторий
git clone <your-repo-url>
cd tgbotkowalski

# Создать .env
nano .env
# Вставить настройки, Ctrl+O, Enter, Ctrl+X

# Создать папку для данных
mkdir -p data

# Загрузить PDF (вариант 1: через scp с локального ПК)
# На локальном компьютере:
scp data/bonus.pdf user@server-ip:/home/user/tgbotkowalski/data/

# Загрузить PDF (вариант 2: через wget)
cd data/
wget https://example.com/your-file.pdf -O bonus.pdf
cd ..

# Запустить
docker-compose up -d

# Проверить логи
docker-compose logs -f
```

### Управление на сервере
```bash
# Просмотр статуса
docker-compose ps

# Просмотр логов (последние 100 строк)
docker-compose logs --tail=100

# Просмотр логов в реальном времени
docker-compose logs -f

# Остановить бота
docker-compose down

# Перезапустить
docker-compose restart

# Обновить код и перезапустить
git pull
docker-compose up -d --build

# Просмотр использования ресурсов
docker stats
```

## Git команды

```bash
# Инициализировать репозиторий
git init

# Добавить все файлы
git add .

# Создать коммит
git commit -m "Initial commit: Telegram bot"

# Добавить удаленный репозиторий
git remote add origin https://github.com/your-username/tgbotkowalski.git

# Запушить
git push -u origin main

# Проверить статус
git status

# Посмотреть изменения
git diff

# Обновить с сервера
git pull
```

## Резервное копирование

```bash
# Создать бэкап базы данных
cp data/bot.db data/bot.db.backup_$(date +%Y%m%d)

# Скачать БД с сервера на локальный ПК
scp user@server-ip:/home/user/tgbotkowalski/data/bot.db ./backup/

# Восстановить из бэкапа
cp data/bot.db.backup_20260119 data/bot.db
docker-compose restart
```

## Мониторинг

```bash
# Просмотр логов за последний час
docker-compose logs --since 1h

# Следить за конкретным контейнером
docker logs -f tgbot_kowalski

# Проверка размера базы данных
ls -lh data/bot.db

# Проверка свободного места на диске
df -h

# Проверка использования памяти
free -h
```

## Отладка

```bash
# Войти в контейнер
docker exec -it tgbot_kowalski /bin/sh

# Проверить переменные окружения в контейнере
docker exec tgbot_kowalski env

# Проверить наличие файлов в контейнере
docker exec tgbot_kowalski ls -la /app/data/

# Перезапустить с выводом в консоль (для отладки)
docker-compose up

# Проверить сетевую связность
docker exec tgbot_kowalski ping -c 3 api.telegram.org
```

## Автозапуск (systemd)

Если не используете Docker:

```bash
# Создать systemd service
sudo nano /etc/systemd/system/tgbot.service

# Вставить:
[Unit]
Description=Telegram Lead Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/your-user/tgbotkowalski
Environment="PATH=/home/your-user/tgbotkowalski/venv/bin"
ExecStart=/home/your-user/tgbotkowalski/venv/bin/python -m bot.main
Restart=always

[Install]
WantedBy=multi-user.target

# Сохранить и активировать
sudo systemctl daemon-reload
sudo systemctl enable tgbot
sudo systemctl start tgbot

# Управление
sudo systemctl status tgbot
sudo systemctl stop tgbot
sudo systemctl restart tgbot
sudo journalctl -u tgbot -f
```

## Telegram команды бота

### Для всех пользователей:
- `/start` - запустить бота и начать воронку

### Для администратора:
- `/stats` - посмотреть статистику
- Reply на сообщение пользователя - ответить ему

## Полезные ссылки

- [@BotFather](https://t.me/BotFather) - создание ботов
- [@userinfobot](https://t.me/userinfobot) - получить свой ID
- [@username_to_id_bot](https://t.me/username_to_id_bot) - получить ID канала
- [Telegram Bot API Docs](https://core.telegram.org/bots/api)
- [aiogram Documentation](https://docs.aiogram.dev/)

## Troubleshooting

### Бот не запускается
```bash
# Проверить конфигурацию
python check_config.py

# Проверить логи
docker-compose logs

# Проверить переменные окружения
cat .env
```

### Ошибка подключения к Telegram
```bash
# Проверить интернет
ping api.telegram.org

# Проверить токен
# В Telegram: @BotFather → /mybots → выбрать бота → API Token
```

### База данных повреждена
```bash
# Восстановить из бэкапа
cp data/bot.db.backup_YYYYMMDD data/bot.db
docker-compose restart
```

### Нехватка места на диске
```bash
# Очистить Docker
docker system prune -a

# Очистить старые логи
docker-compose logs --tail=0 > /dev/null

# Удалить старые бэкапы
rm data/*.backup_*
```
