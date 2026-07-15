import json
import telebot
from telebot import types
import requests
import time

with open('bot_settings.json', 'r') as f:
    settings = json.load(f)

BOT_TOKEN = settings['bot_token']
ADMIN_ID = str(settings['admin_telegram_id'])
API_URL = 'http://keycodm.atwebpages.com/bot_api.php'
WALLETS = settings['usdt_wallets']
PRICES = settings['prices']
APK_URL = settings.get('apk_url', 'http://keycodm.atwebpages.com/app.apk')

# KILL ALL OTHER INSTANCES
requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook')
time.sleep(2)
requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset=-1')
time.sleep(1)

bot = telebot.TeleBot(BOT_TOKEN)

print("🤖 Bot starting...")

def call_api(action, **params):
    params['action'] = action
    try:
        r = requests.get(API_URL, params=params, timeout=10)
        return r.json()
    except:
        return {'error': 'Server error'}

@bot.message_handler(commands=['start'])
def start(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("FREE Trial", "Buy Plan", "Profile", "Support")
    bot.send_message(msg.chat.id, "CODM ELITE SHOP", reply_markup=kb)

@bot.message_handler(commands=['buy'])
def buy(msg):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("FREE Trial", callback_data="trial"),
        types.InlineKeyboardButton("Week - 15$", callback_data="week"),
        types.InlineKeyboardButton("Month - 30$", callback_data="month")
    )
    bot.send_message(msg.chat.id, "Choose plan:", reply_markup=kb)

@bot.message_handler(commands=['profile'])
def profile(msg):
    d = call_api('profile', user_id=str(msg.from_user.id))
    t = "USED" if d.get('has_trial') else "AVAILABLE"
    bot.send_message(msg.chat.id, f"Trial: {t}")

@bot.message_handler(commands=['test'])
def test(msg):
    if str(msg.chat.id) != ADMIN_ID:
        return
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("Test Trial", callback_data="adm_trial"),
        types.InlineKeyboardButton("Test Week", callback_data="adm_week"),
        types.InlineKeyboardButton("Test Month", callback_data="adm_month")
    )
    bot.send_message(msg.chat.id, "ADMIN TEST", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text and "Trial" in m.text)
def t_trial(msg):
    d = call_api('get_trial', user_id=str(msg.from_user.id))
    if d.get('key'):
        bot.send_message(msg.chat.id, f"KEY: {d['key']}\nAPK: {APK_URL}")
    else:
        bot.send_message(msg.chat.id, d.get('error','Error'))

@bot.message_handler(func=lambda m: m.text and "Buy" in m.text)
def t_buy(msg): buy(msg)

@bot.message_handler(func=lambda m: m.text and "Profile" in m.text)
def t_profile(msg): profile(msg)

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    d = call.data
    if d == 'trial':
        r = call_api('get_trial', user_id=str(call.from_user.id))
        if r.get('key'):
            bot.send_message(call.message.chat.id, f"KEY: {r['key']}\nAPK: {APK_URL}")
            bot.answer_callback_query(call.id, "Sent!")
        else:
            bot.answer_callback_query(call.id, r.get('error','Error'), show_alert=True)
    elif d in ['week', 'month']:
        price = PRICES.get(d, 15)
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("TON", callback_data=f"net_{d}_TON"),
            types.InlineKeyboardButton("TRC20", callback_data=f"net_{d}_TRC20")
        )
        kb.add(types.InlineKeyboardButton("GET KEY", callback_data=f"get_{d}"))
        bot.edit_message_text(f"{d.upper()} - {price}$\n\nChoose network:", call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif d.startswith('net_'):
        _, plan, net = d.split('_')
        wallet = WALLETS.get(net, 'Not set')
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("GET KEY", callback_data=f"get_{plan}"))
        bot.edit_message_text(f"Send {PRICES.get(plan,15)}$ USDT\n{net}: {wallet}\n\nClick GET KEY", call.message.chat.id, call.message.message_id, reply_markup=kb)
    elif d.startswith('get_'):
        plan = d.replace('get_', '')
        r = call_api('get_paid_key', type=plan, user_id=str(call.from_user.id))
        if r.get('key'):
            dur = '30d' if plan == 'month' else '7d'
            bot.send_message(call.message.chat.id, f"KEY: {r['key']}\n{dur}\nAPK: {APK_URL}")
            bot.edit_message_text("Sent!", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, r.get('error','Error'), show_alert=True)
    elif d.startswith('adm_'):
        if str(call.from_user.id) != ADMIN_ID: return
        plan = d.replace('adm_', '')
        act = 'get_trial' if plan == 'trial' else 'get_paid_key'
        r = call_api(act, type=plan, user_id='admin')
        if r.get('key'):
            bot.send_message(call.message.chat.id, f"TEST: {r['key']}")
            bot.answer_callback_query(call.id, "Sent!")

print("✅ Ready!")
bot.polling(none_stop=True)