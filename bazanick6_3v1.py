import asyncio
import json
import os
import logging
import sys
import aiohttp
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

# --- НАСТРОЙКИ ---
API_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN_HERE'
ITEMS_PER_PAGE = 10
TEMP_FOLDER = "reports"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Создаем папку для отчетов, если её нет
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

# Хранилище результатов быстрого поиска {username: [sites]}
search_cache = {}

# --- БЫСТРЫЙ ПОИСК (WhatsMyName) ---

SITES_TO_CHECK = [
    {
        'name': 'GitHub',
        'url': 'https://github.com/{username}',
        'check': lambda text, status: status == 200 and 'Page not found' not in text and 'This organization has no public members' not in text
    },
    {
        'name': 'Twitter/X',
        'url': 'https://twitter.com/{username}',
        'check': lambda text, status: status == 200 and 'This account doesn\'t exist' not in text and 'This page is no longer available' not in text
    },
    {
        'name': 'Instagram',
        'url': 'https://www.instagram.com/{username}/',
        'check': lambda text, status: status == 200 and 'Page Not Found' not in text and 'Sorry, this page isn\'t available' not in text
    },
    {
        'name': 'Reddit',
        'url': 'https://www.reddit.com/user/{username}',
        'check': lambda text, status: status == 200 and 'Page not found' not in text and 'does not exist' not in text
    },
    {
        'name': 'YouTube',
        'url': 'https://www.youtube.com/@{username}',
        'check': lambda text, status: status == 200 and 'Not Found' not in text and 'Channel does not exist' not in text
    },
    {
        'name': 'TikTok',
        'url': 'https://www.tiktok.com/@{username}',
        'check': lambda text, status: status == 200 and 'Couldn\'t find this account' not in text
    },
    {
        'name': 'Facebook',
        'url': 'https://www.facebook.com/{username}',
        'check': lambda text, status: status == 200 and 'Page not found' not in text and 'content not found' not in text
    },
    {
        'name': 'LinkedIn',
        'url': 'https://www.linkedin.com/in/{username}',
        'check': lambda text, status: status == 200 and 'Page not found' not in text and 'This profile is not available' not in text
    },
    {
        'name': 'Pinterest',
        'url': 'https://www.pinterest.com/{username}/',
        'check': lambda text, status: status == 200 and 'Page not found' not in text
    },
    {
        'name': 'Tumblr',
        'url': 'https://{username}.tumblr.com',
        'check': lambda text, status: status == 200 and 'There\'s nothing here' not in text and 'Page not found' not in text
    },
    {
        'name': 'VK',
        'url': 'https://vk.com/{username}',
        'check': lambda text, status: status == 200 and 'К сожалению, запрошенная страница не найдена' not in text and 'Page not found' not in text
    },
    {
        'name': 'Telegram',
        'url': 'https://t.me/{username}',
        'check': lambda text, status: status == 200 and 'If you have Telegram' in text and 'Sorry, this username doesn\'t exist' not in text
    },
    {
        'name': 'Steam',
        'url': 'https://steamcommunity.com/id/{username}',
        'check': lambda text, status: status == 200 and 'The specified profile could not be found' not in text
    },
    {
        'name': 'Spotify',
        'url': 'https://open.spotify.com/user/{username}',
        'check': lambda text, status: status == 200 and 'Page not found' not in text
    },
    {
        'name': 'SoundCloud',
        'url': 'https://soundcloud.com/{username}',
        'check': lambda text, status: status == 200 and 'Sorry! We couldn\'t find that track' not in text and 'Page not found' not in text
    },
    {
        'name': 'Medium',
        'url': 'https://medium.com/@{username}',
        'check': lambda text, status: status == 200 and 'Page not found' not in text and ('Member-only' in text or 'stories' in text)
    },
    {
        'name': 'DeviantArt',
        'url': 'https://www.deviantart.com/{username}',
        'check': lambda text, status: status == 200 and 'DeviantArt - The Largest Online Art Gallery' in text
    },
    {
        'name': 'Flickr',
        'url': 'https://www.flickr.com/people/{username}/',
        'check': lambda text, status: status == 200 and 'Page not found' not in text
    },
    {
        'name': 'Imgur',
        'url': 'https://imgur.com/user/{username}',
        'check': lambda text, status: status == 200 and 'Page not found' not in text
    },
    {
        'name': 'Patreon',
        'url': 'https://www.patreon.com/{username}',
        'check': lambda text, status: status == 200 and 'Page not found' not in text
    },
    {
        'name': 'Twitch',
        'url': 'https://www.twitch.tv/{username}',
        'check': lambda text, status: status == 200 and 'Sorry. Unless you\'ve got a time machine' not in text
    },
    {
        'name': 'WordPress',
        'url': 'https://{username}.wordpress.com',
        'check': lambda text, status: status == 200 and 'Page not found' not in text
    },
    {
        'name': 'Blogger',
        'url': 'https://{username}.blogspot.com',
        'check': lambda text, status: status == 200 and 'Not Found' not in text
    },
    {
        'name': 'Dribbble',
        'url': 'https://dribbble.com/{username}',
        'check': lambda text, status: status == 200 and 'Page not found' not in text
    },
    {
        'name': 'Behance',
        'url': 'https://www.behance.net/{username}',
        'check': lambda text, status: status == 200 and 'Page not found' not in text
    },
    {
        'name': 'Mixcloud',
        'url': 'https://www.mixcloud.com/{username}/',
        'check': lambda text, status: status == 200 and 'Page not found' not in text
    },
    {
        'name': 'Mastodon',
        'url': 'https://mastodon.social/@{username}',
        'check': lambda text, status: status == 200 and 'Account not found' not in text
    },
    {
        'name': 'Bluesky',
        'url': 'https://bsky.app/profile/{username}',
        'check': lambda text, status: status == 200 and 'Profile not found' not in text
    },
    {
        'name': 'Threads',
        'url': 'https://www.threads.net/@{username}',
        'check': lambda text, status: status == 200 and 'Page Not Found' not in text
    },
    {
        'name': 'Gravatar',
        'url': 'https://en.gravatar.com/{username}',
        'check': lambda text, status: status == 200 and 'Not Found' not in text
    },
    {
        'name': 'Snapchat',
        'url': 'https://www.snapchat.com/add/{username}',
        'check': lambda text, status: status == 200 and 'Sorry! We couldn\'t find that user' not in text
    },
    {
        'name': 'Wikipedia',
        'url': 'https://en.wikipedia.org/wiki/{username}',
        'check': lambda text, status: status == 200 and 'does not have a page' not in text and 'Page not found' not in text
    },
    {
        'name': 'GitLab',
        'url': 'https://gitlab.com/{username}',
        'check': lambda text, status: status == 200 and 'Page not found' not in text
    },
    {
        'name': 'Bitbucket',
        'url': 'https://bitbucket.org/{username}',
        'check': lambda text, status: status == 200 and 'Page not found' not in text
    },
    {
        'name': 'HackerNews',
        'url': 'https://news.ycombinator.com/user?id={username}',
        'check': lambda text, status: status == 200 and 'No such user' not in text
    },
    {
        'name': 'ProductHunt',
        'url': 'https://www.producthunt.com/@{username}',
        'check': lambda text, status: status == 200 and 'Page not found' not in text
    },
    {
        'name': 'Keybase',
        'url': 'https://keybase.io/{username}',
        'check': lambda text, status: status == 200 and 'Page not found' not in text
    },
    {
        'name': 'Vimeo',
        'url': 'https://vimeo.com/{username}',
        'check': lambda text, status: status == 200 and 'Page not found' not in text
    },
    {
        'name': 'OK.ru',
        'url': 'https://ok.ru/{username}',
        'check': lambda text, status: status == 200 and 'Страница не найдена' not in text
    },
    {
        'name': 'Rutube',
        'url': 'https://rutube.ru/{username}',
        'check': lambda text, status: status == 200 and 'Страница не найдена' not in text
    },
]

async def check_site(session, site, username):
    """Проверяет один сайт с анализом содержимого"""
    try:
        url = site['url'].replace('{username}', username)
        async with session.get(
            url, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }, 
            allow_redirects=True, 
            timeout=8
        ) as response:
            status = response.status
            
            if status != 200:
                return None
            
            text = await response.text()
            
            if site['check'](text, status):
                return {
                    'name': site['name'],
                    'url': url
                }
    except asyncio.TimeoutError:
        pass
    except Exception:
        pass
    return None

async def whatsmyname_search(username):
    """Быстрый поиск через прямые запросы к сайтам (WhatsMyName)"""
    found_sites = []
    
    connector = aiohttp.TCPConnector(limit=20, limit_per_host=3)
    timeout = aiohttp.ClientTimeout(total=15, connect=5)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        for site in SITES_TO_CHECK:
            tasks.append(check_site(session, site, username))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if result and isinstance(result, dict):
                found_sites.append(result)
    
    return found_sites

# --- ПОИСК SHERLOCK ---

async def sherlock_search(username, message, status_msg):
    """Запускает Sherlock поиск"""
    # Путь к Sherlock
    sherlock_exe = r"C:\Users\Пользователь\AppData\Roaming\Python\Python311\Scripts\sherlock.exe"
    
    # Проверяем, существует ли Sherlock
    if not os.path.exists(sherlock_exe):
        await status_msg.edit_text(
            "Ошибка: Sherlock не найден!\n\n"
            "Проверьте установку:\n"
            "pip install sherlock-project"
        )
        return None
    
    # Создаем папку для отчетов, если её нет
    if not os.path.exists(TEMP_FOLDER):
        os.makedirs(TEMP_FOLDER)
    
    # Запускаем Sherlock
    cmd_args = [
        sherlock_exe,
        username,
        "--folderoutput", os.path.abspath(TEMP_FOLDER),
        "--no-color",
        "--print-found"
    ]
    
    logging.info(f"Запуск Sherlock: {' '.join(cmd_args)}")
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.path.dirname(sherlock_exe)
        )
        
        stdout, stderr = await process.communicate()
        
        if stdout:
            logging.info(f"Sherlock stdout: {stdout.decode('utf-8', errors='ignore')[:500]}")
        if stderr:
            logging.warning(f"Sherlock stderr: {stderr.decode('utf-8', errors='ignore')[:500]}")
            
        if process.returncode != 0:
            logging.error(f"Sherlock завершился с кодом: {process.returncode}")
            return None
            
    except Exception as e:
        logging.error(f"Ошибка запуска Sherlock: {e}")
        await status_msg.edit_text(
            "Ошибка при запуске Sherlock.\n\n"
            "Проверьте установку:\n"
            "pip install sherlock-project"
        )
        return None
    
    # Ищем TXT файл с результатами
    txt_file = None
    if os.path.exists(TEMP_FOLDER):
        for filename in os.listdir(TEMP_FOLDER):
            if filename.startswith(username) and filename.endswith(".txt"):
                txt_file = os.path.join(TEMP_FOLDER, filename)
                break
    
    if not txt_file or not os.path.exists(txt_file):
        logging.warning(f"TXT файл не найден для {username}")
        return None
    
    # Парсим TXT файл
    results = []
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Ищем все URL в формате https:// или http://
            urls = re.findall(r'https?://[^\s]+', content)
            
            for url in urls:
                # Извлекаем название сайта из URL
                site_name = url.split('//')[1].split('/')[0]
                # Убираем www.
                site_name = site_name.replace('www.', '')
                # Берем только домен первого уровня
                site_name = site_name.split('.')[0].capitalize()
                
                results.append({
                    'site': site_name,
                    'url': url
                })
            
            logging.info(f"Найдено {len(results)} ссылок через регулярные выражения")
            
    except Exception as e:
        logging.error(f"Ошибка парсинга TXT: {e}")
        return None
    
    logging.info(f"Sherlock найдено {len(results)} аккаунтов для {username}")
    return results

# --- МЕДЛЕННЫЙ ПОИСК (Maigret) ---

def find_report_file(username, extension):
    """Ищет файл отчета в папке reports"""
    expected_prefix = f"report_{username}"
    if os.path.exists(TEMP_FOLDER):
        for filename in os.listdir(TEMP_FOLDER):
            if filename.startswith(expected_prefix) and filename.endswith(extension):
                return os.path.join(TEMP_FOLDER, filename)
    return None

def get_maigret_data(username):
    """Читает JSON и вытаскивает ссылки"""
    json_path = find_report_file(username, ".json")
    results = []
    
    if json_path and os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                target_data = data.get(username, data)
                
                if isinstance(target_data, dict):
                    for site_name, site_info in target_data.items():
                        if isinstance(site_info, dict):
                            url = site_info.get('url_user')
                            status = site_info.get('status', {}).get('id')
                            
                            if url and (status == 'found' or 'url_user' in site_info):
                                results.append({
                                    'site': site_name,
                                    'url': url
                                })
        except Exception as e:
            logging.error(f"Ошибка парсинга JSON: {e}")
    return results

async def maigret_search(username, message, status_msg):
    """Запускает Maigret поиск"""
    cmd_args = [
        sys.executable, "-m", "maigret", 
        username,
        "--folder", TEMP_FOLDER,
        "--json", "simple", 
        "--txt", 
        "--no-progressbar"
    ]
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    logging.info(f"Запуск Maigret: {' '.join(cmd_args)}")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env 
        )
        
        stdout, stderr = await process.communicate()
        
        if stderr and b"ERROR" in stderr:
            logging.warning(f"Maigret log: {stderr.decode(errors='ignore')}")

    except Exception as e:
        logging.error(f"Ошибка запуска Maigret: {e}")
        await status_msg.edit_text("Ошибка при запуске Maigret.")
        return None

    results = get_maigret_data(username)
    txt_report = find_report_file(username, ".txt")

    if not results and not txt_report:
        return None

    # Отправка файла
    if txt_report:
        try:
            file = FSInputFile(txt_report)
            await message.answer_document(file, caption=f"Отчет Maigret: {username}")
        except Exception as e:
            logging.error(f"Ошибка отправки файла: {e}")

    return results

# --- ОБЩИЕ ФУНКЦИИ ---

def generate_keyboard_quick(username, total_items, page=0):
    """Генерирует клавиатуру для быстрого поиска"""
    builder = InlineKeyboardBuilder()
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    row_btns = []
    if page > 0:
        row_btns.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"qnav:{username}:{page-1}"))
    if page < total_pages - 1:
        row_btns.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"qnav:{username}:{page+1}"))
    
    if row_btns:
        builder.row(*row_btns)
    
    builder.row(InlineKeyboardButton(text="📥 Скачать TXT", callback_data=f"qdownload:{username}"))
    return builder.as_markup()

async def show_page_quick(message_or_call, username, page):
    """Показывает страницу с результатами быстрого поиска"""
    results = search_cache.get(username, [])
    if not results:
        if isinstance(message_or_call, types.CallbackQuery):
            await message_or_call.answer("Результаты устарели. Запустите поиск заново.", show_alert=True)
        return
    
    total = len(results)
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    if page >= total_pages:
        page = total_pages - 1
    
    start = page * ITEMS_PER_PAGE
    end = min(start + ITEMS_PER_PAGE, total)
    page_items = results[start:end]
    
    text = f"🔍 WhatsMyName — быстрая проверка ~40 сайтов\n✅ Найдено {total} аккаунтов для {username}\n\n"
    for item in page_items:
        text += f"🔹 <a href='{item['url']}'>{item['name']}</a>\n"
    
    text += f"\n📄 Страница {page + 1} из {total_pages}"
    
    keyboard = generate_keyboard_quick(username, total, page)

    try:
        if isinstance(message_or_call, types.CallbackQuery):
            await message_or_call.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
            await message_or_call.answer()
        else:
            await message_or_call.answer(text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise e

async def download_quick_results(username, message):
    """Скачивает результаты WhatsMyName в TXT файл"""
    results = search_cache.get(username, [])
    if not results:
        await message.answer("❌ Результаты не найдены")
        return
    
    # Создаем TXT файл
    txt_file = os.path.join(TEMP_FOLDER, f"whatsmyname_{username}.txt")
    try:
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"Результаты поиска WhatsMyName для {username}\n")
            f.write(f"Найдено аккаунтов: {len(results)}\n")
            f.write("=" * 50 + "\n\n")
            for item in results:
                f.write(f"{item['name']}: {item['url']}\n")
        
        # Отправляем файл
        file = FSInputFile(txt_file)
        await message.answer_document(file, caption=f"📊 Результаты WhatsMyName для {username}")
        
        # Удаляем временный файл
        os.remove(txt_file)
        
    except Exception as e:
        logging.error(f"Ошибка создания TXT файла: {e}")
        await message.answer("❌ Ошибка при создании файла")

def generate_keyboard_sherlock(username, total_items, page=0):
    """Генерирует клавиатуру для Sherlock"""
    builder = InlineKeyboardBuilder()
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    row_btns = []
    if page > 0:
        row_btns.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"snav:{username}:{page-1}"))
    if page < total_pages - 1:
        row_btns.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"snav:{username}:{page+1}"))
    
    if row_btns:
        builder.row(*row_btns)
    
    builder.row(InlineKeyboardButton(text="📥 Скачать TXT", callback_data=f"sdownload:{username}"))
    return builder.as_markup()

async def show_page_sherlock(message_or_call, username, results, page):
    """Показывает страницу с результатами Sherlock"""
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_items = results[start:end]
    
    total = len(results)
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    text = f"🔎 Sherlock — поиск по 400+ сайтам\n✅ Найдено {total} аккаунтов для {username}\n\n"
    for item in page_items:
        text += f"🔹 <a href='{item['url']}'>{item['site']}</a>\n"
    
    text += f"\n📄 Страница {page+1} из {total_pages}"
    
    keyboard = generate_keyboard_sherlock(username, total, page)

    try:
        if isinstance(message_or_call, types.CallbackQuery):
            await message_or_call.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
        else:
            await message_or_call.answer(text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
    except TelegramBadRequest:
        if isinstance(message_or_call, types.CallbackQuery):
            await message_or_call.answer()

async def download_sherlock_results(username, message):
    """Скачивает результаты Sherlock в TXT файл"""
    # Ищем TXT файл Sherlock
    txt_file = None
    if os.path.exists(TEMP_FOLDER):
        for filename in os.listdir(TEMP_FOLDER):
            if filename.startswith(username) and filename.endswith(".txt"):
                txt_file = os.path.join(TEMP_FOLDER, filename)
                break
    
    if not txt_file or not os.path.exists(txt_file):
        await message.answer("❌ Файл с результатами не найден")
        return
    
    try:
        # Отправляем файл
        file = FSInputFile(txt_file)
        await message.answer_document(file, caption=f"📊 Результаты Sherlock для {username}")
        
    except Exception as e:
        logging.error(f"Ошибка отправки файла Sherlock: {e}")
        await message.answer("❌ Ошибка при отправке файла")

def generate_keyboard_maigret(username, total_items, page=0):
    """Генерирует клавиатуру для Maigret"""
    builder = InlineKeyboardBuilder()
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    row_btns = []
    if page > 0:
        row_btns.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"mnav:{username}:{page-1}"))
    if page < total_pages - 1:
        row_btns.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"mnav:{username}:{page+1}"))
    
    if row_btns:
        builder.row(*row_btns)
    
    builder.row(InlineKeyboardButton(text="📥 Скачать TXT", callback_data=f"mdownload:{username}"))
    return builder.as_markup()

async def show_page_maigret(message_or_call, username, results, page):
    """Показывает страницу с результатами Maigret"""
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_items = results[start:end]
    
    total = len(results)
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    text = f"🐌 Maigret — глубокий анализ ~300 сайтов\n✅ Найдено {total} аккаунтов для {username}\n\n"
    for item in page_items:
        text += f"🔹 <a href='{item['url']}'>{item['site']}</a>\n"
    
    text += f"\n📄 Страница {page+1} из {total_pages}"
    
    keyboard = generate_keyboard_maigret(username, total, page)

    try:
        if isinstance(message_or_call, types.CallbackQuery):
            await message_or_call.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
        else:
            await message_or_call.answer(text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
    except TelegramBadRequest:
        if isinstance(message_or_call, types.CallbackQuery):
            await message_or_call.answer()

async def download_maigret_results(username, message):
    """Скачивает результаты Maigret в TXT файл"""
    # Ищем TXT файл Maigret
    txt_file = find_report_file(username, ".txt")
    
    if not txt_file or not os.path.exists(txt_file):
        await message.answer("❌ Файл с результатами не найден")
        return
    
    try:
        # Отправляем файл
        file = FSInputFile(txt_file)
        await message.answer_document(file, caption=f"📊 Результаты Maigret для {username}")
        
    except Exception as e:
        logging.error(f"Ошибка отправки файла Maigret: {e}")
        await message.answer("❌ Ошибка при отправке файла")

# --- ХЕНДЛЕРЫ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я ищу аккаунты по никнейму.\n\n"
        "🔍 Доступны три метода поиска:\n"
        "• WhatsMyName — быстрая проверка ~40 сайтов (20-40 сек)\n"
        "• Sherlock — поиск по 400+ сайтам (1-2 мин)\n"
        "• Maigret — глубокий анализ ~300 сайтов (2-4 мин)\n\n"
        "Просто отправь никнейм и выбери метод!"
    )

@dp.message(F.text)
async def handle_username(message: types.Message):
    username = message.text.strip()
    
    if len(username) < 2:
        await message.answer("⚠️ Ник слишком короткий.")
        return
    
    if not username.replace('_','').replace('-','').replace('.','').isalnum():
        await message.answer("⚠️ Некорректные символы.")
        return

    # Создаем клавиатуру с тремя методами
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔍 WhatsMyName", callback_data=f"whatsmyname:{username}"),
        InlineKeyboardButton(text="🔎 Sherlock", callback_data=f"sherlock:{username}"),
        InlineKeyboardButton(text="🐌 Maigret", callback_data=f"maigret:{username}")
    )
    
    await message.answer(
        f"🔍 Выбери метод поиска для {username}:",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("whatsmyname:"))
async def process_whatsmyname_search(callback: CallbackQuery):
    _, username = callback.data.split(":", 1)
    
    await callback.message.edit_text(
        f"🔍 WhatsMyName — быстрая проверка ~40 сайтов\n"
        f"👤 Ищу {username}\n"
        f"⏱ Ждите 20-40 секунд"
    )
    
    await callback.answer()

    try:
        results = await whatsmyname_search(username)
        search_cache[username] = results
        
        if not results:
            await callback.message.edit_text(
                f"❌ Аккаунт {username} не найден ни на одном сайте.\n\n"
                f"💡 Попробуйте использовать Sherlock или Maigret для более глубокого поиска."
            )
            return
        
        await show_page_quick(callback.message, username, 0)
        
    except Exception as e:
        logging.error(f"Ошибка WhatsMyName: {e}")
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}")

@dp.callback_query(F.data.startswith("sherlock:"))
async def process_sherlock_search(callback: CallbackQuery):
    _, username = callback.data.split(":", 1)
    
    status_msg = await callback.message.edit_text(
        f"🔎 Sherlock — поиск по 400+ сайтам\n"
        f"👤 Ищу {username}\n"
        f"⏱ Ждите 1-2 минуты..."
    )
    
    await callback.answer()

    results = await sherlock_search(username, callback.message, status_msg)
    
    if results is None:
        await status_msg.edit_text(
            f"❌ Ничего не найдено для {username}.\n\n"
            f"💡 Попробуйте Maigret для более глубокого анализа."
        )
        return
    
    if results:
        await show_page_sherlock(status_msg, username, results, 0)
    else:
        await status_msg.edit_text(
            f"❌ Аккаунт {username} не найден.\n\n"
            f"💡 Возможно, никнейм не существует."
        )

@dp.callback_query(F.data.startswith("maigret:"))
async def process_maigret_search(callback: CallbackQuery):
    _, username = callback.data.split(":", 1)
    
    status_msg = await callback.message.edit_text(
        f"🐌 Maigret — глубокий анализ ~300 сайтов\n"
        f"👤 Ищу {username}\n"
        f"⏱ Ждите 2-4 минуты..."
    )
    
    await callback.answer()

    results = await maigret_search(username, callback.message, status_msg)
    
    if results is None:
        await status_msg.edit_text(
            f"❌ Ничего не найдено для {username}."
        )
        return
    
    if results:
        await show_page_maigret(status_msg, username, results, 0)
    else:
        await status_msg.edit_text(
            f"❌ Аккаунт {username} не найден.\n\n"
            f"💡 Возможно, никнейм не существует."
        )

# --- СКАЧИВАНИЕ ФАЙЛОВ ---

# Для WhatsMyName
@dp.callback_query(F.data.startswith("qdownload:"))
async def process_quick_download(callback: CallbackQuery):
    _, username = callback.data.split(":", 1)
    await callback.answer("⏳ Создаю файл...")
    await download_quick_results(username, callback.message)

# Для Sherlock
@dp.callback_query(F.data.startswith("sdownload:"))
async def process_sherlock_download(callback: CallbackQuery):
    _, username = callback.data.split(":", 1)
    await callback.answer("⏳ Подготавливаю файл...")
    await download_sherlock_results(username, callback.message)

# Для Maigret
@dp.callback_query(F.data.startswith("mdownload:"))
async def process_maigret_download(callback: CallbackQuery):
    _, username = callback.data.split(":", 1)
    await callback.answer("⏳ Подготавливаю файл...")
    await download_maigret_results(username, callback.message)

# --- НАВИГАЦИЯ ---

# Для WhatsMyName
@dp.callback_query(F.data.startswith("qnav:"))
async def process_quick_navigation(callback: CallbackQuery):
    _, username, page = callback.data.split(":")
    page = int(page)
    
    results = search_cache.get(username, [])
    if not results:
        await callback.answer("Результаты устарели. Запустите поиск заново.", show_alert=True)
        return
    
    total_pages = (len(results) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    if page >= total_pages:
        page = total_pages - 1
    
    await show_page_quick(callback, username, page)

# Для Sherlock
@dp.callback_query(F.data.startswith("snav:"))
async def process_sherlock_navigation(callback: CallbackQuery):
    _, username, page = callback.data.split(":")
    page = int(page)
    
    # Перечитываем данные из TXT файла
    results = []
    if os.path.exists(TEMP_FOLDER):
        for filename in os.listdir(TEMP_FOLDER):
            if filename.startswith(username) and filename.endswith(".txt"):
                txt_file = os.path.join(TEMP_FOLDER, filename)
                try:
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        urls = re.findall(r'https?://[^\s]+', content)
                        for url in urls:
                            site_name = url.split('//')[1].split('/')[0].replace('www.', '').split('.')[0].capitalize()
                            results.append({
                                 'site': site_name,
                                'url': url
                            })
                except Exception as e:
                    logging.error(f"Ошибка чтения Sherlock TXT: {e}")
                break
    
    if results:
        await show_page_sherlock(callback, username, results, page)
    else:
        await callback.answer("Данные устарели.", show_alert=True)
    await callback.answer()

# Для Maigret
@dp.callback_query(F.data.startswith("mnav:"))
async def process_maigret_navigation(callback: CallbackQuery):
    _, username, page = callback.data.split(":")
    page = int(page)
    
    results = get_maigret_data(username)
    if results:
        await show_page_maigret(callback, username, results, page)
    else:
        await callback.answer("Данные устарели.", show_alert=True)
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
