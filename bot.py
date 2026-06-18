import json
import os
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "8676096132:AAE0LDxXgNk4_8n0waZtf-6aiQR0g1-lnx8"
ADMIN_ID = 6634773779
DATA_FILE = "applications.json"

def load_applications():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"applications": [], "next_id": 1}

def save_applications(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_applications():
    return load_applications()["applications"]

def get_next_id():
    data = load_applications()
    return data["next_id"]

def increment_id():
    data = load_applications()
    data["next_id"] += 1
    save_applications(data)

def add_application(app_data):
    data = load_applications()
    app_id = data["next_id"]
    app_data["id"] = app_id
    app_data["status"] = "new"
    app_data["date"] = datetime.now().strftime("%d.%m.%Y %H:%M")
    data["applications"].append(app_data)
    save_applications(data)
    increment_id()
    return app_id

def update_application_status(app_id, new_status):
    data = load_applications()
    for app in data["applications"]:
        if app["id"] == app_id:
            app["status"] = new_status
            save_applications(data)
            return True
    return False

def delete_application(app_id):
    data = load_applications()
    for i, app in enumerate(data["applications"]):
        if app["id"] == app_id:
            del data["applications"][i]
            save_applications(data)
            return True
    return False

def get_status_buttons(app_id, status):
    buttons = []
    if status == "new":
        buttons = [
            [InlineKeyboardButton("✅ Взять в работу", callback_data=f"in_progress_{app_id}")],
            [InlineKeyboardButton("⏰ Отложить", callback_data=f"delayed_{app_id}")],
            [InlineKeyboardButton("❌ Отклонить", callback_data=f"cancelled_{app_id}")]
        ]
    elif status == "in_progress":
        buttons = [
            [InlineKeyboardButton("✅ Выполнена", callback_data=f"done_{app_id}")],
            [InlineKeyboardButton("⏰ Отложить", callback_data=f"delayed_{app_id}")]
        ]
    elif status == "delayed":
        buttons = [
            [InlineKeyboardButton("✅ Взять в работу", callback_data=f"in_progress_{app_id}")],
            [InlineKeyboardButton("✅ Выполнена", callback_data=f"done_{app_id}")]
        ]
    elif status == "done" or status == "cancelled":
        buttons = [
            [InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_{app_id}")]
        ]
    buttons.append([InlineKeyboardButton("📋 Все заявки", callback_data="list")])
    return InlineKeyboardMarkup(buttons)

def format_application(app):
    status_emoji = {"new": "🟢", "in_progress": "🟡", "delayed": "🔴", "done": "✅", "cancelled": "❌"}
    status_text = {"new": "Новая", "in_progress": "В работе", "delayed": "Отложена", "done": "Выполнена", "cancelled": "Отклонена"}
    text = f"""
🔔 *ЗАЯВКА #{app['id']}*

👤 *Имя:* {app.get('name', 'Не указано')}
📱 *Телефон:* {app.get('phone', 'Не указан')}
📟 *Устройство:* {app.get('device', 'Не указан')}
📱 *Модель:* {app.get('model', 'Не указана')}
💼 *Услуга:* {app.get('service', 'Не указана')}
💰 *Цена:* {app.get('price', 'Не указана')}
🕐 *Время:* {app.get('date', 'Не указано')}
📊 *Статус:* {status_emoji.get(app['status'], '')} {status_text.get(app['status'], 'Неизвестен')}
"""
    return text

def parse_application_from_message(text):
    data = {}
    name_match = re.search(r'Имя:\s*(.+?)(?:\n|$)', text)
    phone_match = re.search(r'Телефон:\s*(.+?)(?:\n|$)', text)
    device_match = re.search(r'Тип устройства:\s*(.+?)(?:\n|$)', text)
    model_match = re.search(r'Модель:\s*(.+?)(?:\n|$)', text)
    service_match = re.search(r'Услуга:\s*(.+?)(?:\n|$)', text)
    price_match = re.search(r'Цена:\s*(.+?)(?:\n|$)', text)
    if name_match:
        data['name'] = name_match.group(1).strip()
    if phone_match:
        data['phone'] = phone_match.group(1).strip()
    if device_match:
        data['device'] = device_match.group(1).strip()
    if model_match:
        data['model'] = model_match.group(1).strip()
    if service_match:
        data['service'] = service_match.group(1).strip()
    if price_match:
        data['price'] = price_match.group(1).strip()
    return data

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = update.message.text
    if "Новая заявка" in text or ("Имя:" in text and "Телефон:" in text):
        app_data = parse_application_from_message(text)
        if app_data.get('name') and app_data.get('phone'):
            app_id = add_application(app_data)
            apps = get_applications()
            app = next((a for a in apps if a["id"] == app_id), None)
            if app:
                formatted_text = format_application(app)
                buttons = get_status_buttons(app_id, "new")
                await update.message.reply_text(formatted_text, parse_mode="Markdown", reply_markup=buttons)
                await update.message.delete()
                print(f"✅ Заявка #{app_id} сохранена!")
                return
    await update.message.reply_text(
        "🤖 Я умею только принимать заявки.\nИспользуйте команды:\n/list - список заявок\n/stats - статистика\n/help - помощь"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
        return
    text = """
🤖 *FixService | Админ-бот*
Привет! Я помогаю управлять заявками.
📋 *Команды:*
/list - показать все заявки
/list 5 - показать последние 5 заявок
/today - заявки за сегодня
/stats - статистика
/help - помощь
📌 Заявки с сайта приходят автоматически с кнопками.
    """
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = """
📚 *Помощь по командам:*
/list - список всех заявок
/list 5 - последние 5 заявок
/today - заявки за сегодня
/stats - статистика
📌 *Управление заявками:*
При каждой заявке есть кнопки:
• ✅ Взять в работу
• ⏰ Отложить
• ✅ Выполнена
• ❌ Отклонить
• 🗑️ Удалить
📊 *Статусы:*
🟢 Новая
🟡 В работе
🔴 Отложена
✅ Выполнена
❌ Отклонена
    """
    await update.message.reply_text(text, parse_mode="Markdown")

async def list_applications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    command = update.message.text.split()
    limit = None
    if len(command) > 1:
        try:
            limit = int(command[1])
        except:
            pass
    apps = get_applications()
    if not apps:
        await update.message.reply_text("📭 Заявок пока нет.")
        return
    apps = sorted(apps, key=lambda x: x.get("date", ""), reverse=True)
    if limit:
        apps = apps[:limit]
    active_apps = [app for app in apps if app["status"] not in ["done", "cancelled"]]
    if not active_apps:
        await update.message.reply_text("✅ Все заявки обработаны!")
        return
    text = "📋 *Список активных заявок:*\n\n"
    for app in active_apps:
        status_emoji = {"new": "🟢", "in_progress": "🟡", "delayed": "🔴"}.get(app["status"], "")
        text += f"{status_emoji} #{app['id']} | {app.get('name', '')} | {app.get('model', '')}\n"
    text += f"\n─────────────────────\nВсего: {len(active_apps)} активных заявок"
    await update.message.reply_text(text, parse_mode="Markdown")

async def today_applications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    today = datetime.now().strftime("%d.%m.%Y")
    apps = get_applications()
    today_apps = [app for app in apps if app.get("date", "").startswith(today)]
    if not today_apps:
        await update.message.reply_text(f"📭 Заявок за сегодня ({today}) нет.")
        return
    text = f"📋 *Заявки за сегодня ({today}):*\n\n"
    for app in today_apps:
        status_emoji = {"new": "🟢", "in_progress": "🟡", "delayed": "🔴", "done": "✅", "cancelled": "❌"}.get(app["status"], "")
        text += f"{status_emoji} #{app['id']} | {app.get('name', '')} | {app.get('model', '')}\n"
    text += f"\n─────────────────────\nВсего: {len(today_apps)} заявок"
    await update.message.reply_text(text, parse_mode="Markdown")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    apps = get_applications()
    if not apps:
        await update.message.reply_text("📊 Заявок пока нет.")
        return
    total = len(apps)
    new = len([a for a in apps if a["status"] == "new"])
    in_progress = len([a for a in apps if a["status"] == "in_progress"])
    delayed = len([a for a in apps if a["status"] == "delayed"])
    done = len([a for a in apps if a["status"] == "done"])
    cancelled = len([a for a in apps if a["status"] == "cancelled"])
    today = datetime.now().strftime("%d.%m.%Y")
    today_apps = len([a for a in apps if a.get("date", "").startswith(today)])
    text = f"""
📊 *Статистика заявок:*
📌 *Всего:* {total} заявок
🟢 *Новые:* {new}
🟡 *В работе:* {in_progress}
🔴 *Отложены:* {delayed}
✅ *Выполнены:* {done}
❌ *Отклонены:* {cancelled}
📅 *За сегодня:* {today_apps} заявок
    """
    await update.message.reply_text(text, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("⛔ У вас нет доступа к этому боту.")
        return
    data = query.data
    if data == "list":
        apps = get_applications()
        active_apps = [a for a in apps if a["status"] not in ["done", "cancelled"]]
        if not active_apps:
            await query.edit_message_text("✅ Все заявки обработаны!")
            return
        text = "📋 *Список активных заявок:*\n\n"
        for app in active_apps:
            status_emoji = {"new": "🟢", "in_progress": "🟡", "delayed": "🔴"}.get(app["status"], "")
            text += f"{status_emoji} #{app['id']} | {app.get('name', '')} | {app.get('model', '')}\n"
        text += f"\n─────────────────────\nВсего: {len(active_apps)} активных заявок"
        await query.edit_message_text(text, parse_mode="Markdown")
        return
    if "_" in data:
        parts = data.split("_")
        if len(parts) == 2:
            status, app_id_str = parts
            app_id = int(app_id_str)
            if update_application_status(app_id, status):
                apps = get_applications()
                app = next((a for a in apps if a["id"] == app_id), None)
                if app:
                    text = format_application(app)
                    buttons = get_status_buttons(app_id, status)
                    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=buttons)
                    status_text = {"in_progress": "взята в работу 🟡", "done": "выполнена ✅", "delayed": "отложена 🔴", "cancelled": "отклонена ❌"}.get(status, "обновлена")
                    await query.message.reply_text(f"✅ Заявка #{app_id} {status_text}!")
            else:
                await query.edit_message_text(f"❌ Ошибка: заявка #{app_id} не найдена.")
    elif data.startswith("delete_"):
        app_id = int(data.split("_")[1])
        if delete_application(app_id):
            await query.edit_message_text(f"🗑️ Заявка #{app_id} удалена.")
        else:
            await query.edit_message_text(f"❌ Ошибка: заявка #{app_id} не найдена.")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_applications))
    application.add_handler(CommandHandler("today", today_applications))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🚀 Бот запущен и работает!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()