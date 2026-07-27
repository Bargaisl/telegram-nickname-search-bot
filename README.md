# Telegram OSINT Nickname Search & Data Mining Bot 🔎🤖

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Telegram API](https://img.shields.io/badge/Telegram-Bot%20API-blue.svg)](https://core.telegram.org/bots)
[![Asyncio](https://img.shields.io/badge/Asyncio-a-green.svg)](https://docs.python.org/3/library/asyncio.html)

Высокопроизводительный Telegram-бот для автоматизированного поиска и агрегации публичной информации по никнеймам и учетным записям в сети.

---

## ✨ Ключевые архитектурные особенности

- ⚡ **Асинхронность:** Построена на `asyncio` / `aiohttp` для высоконагруженной работы с сетью.
- 🗄️ **Хранение данных:** Интеграция с PostgreSQL 15 и кэшированием результатов в Redis 7.
- 📊 **Формирование отчетов:** Автоматическая сборка результатов и выгрузка отчетов в каталог `reports/`.
- 🔒 **Изоляция конфигурации:** Все секреты и токены вынесены в переменные окружения `.env`.

---

## 🛠️ Стек технологий

* **Язык:** Python 3.10+
* **Сеть & API:** `telebot` / `aiohttp` / `requests`
* **Парсинг:** `BeautifulSoup4`, `lxml`
* **Инфраструктура:** Docker Compose, PostgreSQL, Redis

---

## 🚀 Быстрый запуск

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/Bargaisl/telegram-nickname-search-bot.git
   cd telegram-nickname-search-bot
   ```

2. **Настройте переменные окружения:**
   Создайте `.env` файл на базе примера и укажите ваш токен:
   ```env
   BOT_TOKEN=your_telegram_bot_token_here
   ```

3. **Запустите приложение:**
   ```bash
   python bazanick6_3v1.py
   ```
