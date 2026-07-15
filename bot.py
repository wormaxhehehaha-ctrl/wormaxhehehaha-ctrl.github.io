import json
import telebot
from telebot import types
import requests
import time

BOT_TOKEN = '8886583166:AAEOOLPEX_sDW6ivAwpvesHjGbtDjQa4mi8'

with open('bot_settings.json', 'r') as f:
    settings = json.load(f)

ADMIN_ID = str(settings['admin_telegram_id'])
API_URL = 'http://keycodm.atwebpages.com/bot_api.php'
WALLETS = settings['usdt_wallets']
PRICES = settings['prices']
APK_URL = settings.get('apk_url', 'http://keycodm.atwebpages.com/app.apk')

# ONLY delete webhook, NOT logOut
requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook', timeout=5)
time.sleep(2)

bot = telebot.TeleBot(BOT_TOKEN)
print("🤖 Bot started!")

# Download APK
APK_DATA = None
try:
    resp = requests.get(APK_URL, timeout=30)
    if resp.status_code == 200:
        APK_DATA = resp.content
        print(f"APK: {len(APK_DATA)} bytes")
except:
    print("APK download failed, will send link")

def api(action, **params):
    params['action'] = action
    try:
        r = requests.get(API_URL, params=params, timeout=10)
        return r.json()
    except:
        return {'error': 'Server error'}

def send_apk(chat_id):
    if APK_DATA:
        try:
            bot.send_document(chat_id, APK_DATA, visible_file_name="CODM_ELITE.apk", caption="CODM ELITE")
            return
        except:
            pass
    bot.send_message(chat_id, f"Download APK: {APK_URL}")

# Check TRC20
def check_payment(network, wallet, amount):
    if network == "TRC20":
        try:
            url = f"https://api.trongrid.io/v1/accounts/{wallet}/transactions/trc20?limit=10&only_confirmed=true"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            for tx in data.get('data', []):
                if time.time() - tx.get('block_timestamp', 0)/1000 < 600:
                    if tx.get('to','').lower() == wallet.lower():
                        if int(tx.get('value',0))/1000000 >= amount * 0.95:
                            return True
            return False
        except:
            return False
    return None  # Other networks - manual

# ========== COMMANDS ==========

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
        types.InlineKeyboardButton("Month - 30$", callback_data="month"),
        types.InlineKeyboardButton("Cancel", callback_data="cancel")
    )
    bot.send_message(msg.chat.id, "Choose plan:", reply_markup=kb)

@bot.message_handler(commands=['profile'])
def profile(msg):
    d = api('profile', user_id=str(msg.from_user.id))
    t = "USED" if d.get('has_trial') else "AVAILABLE"
    bot.send_message(msg.chat.id, f"Profile\nID: {msg.from_user.id}\nTrial: {t}")

@bot.message_handler(commands=['support'])
def support(msg):
    bot.send_message(msg.chat.id, "Support: @idkidk1010")

@bot.message_handler(commands=['test'])
def test(msg):
    if str(msg.chat.id) != ADMIN_ID: return
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("Test Trial", callback_data="adm_trial"),
        types.InlineKeyboardButton("Test Week", callback_data="adm_week"),
        types.InlineKeyboardButton("Test Month", callback_data="adm_month")
    )
    bot.send_message(msg.chat.id, "ADMIN TEST", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text and "Trial" in m.text)
def t_trial(msg):
    d = api('get_trial', user_id=str(msg.from_user.id))
    if d.get('key'):
        bot.send_message(msg.chat.id, f"KEY: {d['key']}\n6 hours\n1 device")
        send_apk(msg.chat.id)
    else:
        bot.send_message(msg.chat.id, d.get('error','Error'))

@bot.message_handler(func=lambda m: m.text and "Buy" in m.text)
def t_buy(msg): buy(msg)

@bot.message_handler(func=lambda m: m.text and "Profile" in m.text)
def t_profile(msg): profile(msg)

@bot.message_handler(func=lambda m: m.text and "Support" in m.text)
def t_support(msg): support(msg)

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    d = call.data
    if d == 'cancel':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        return
    if d == 'trial':
        r = api('get_trial', user_id=str(call.from_user.id))
        if r.get('key'):
            bot.send_message(call.message.chat.id, f"KEY: {r['key']}\n6 hours")
            send_apk(call.message.chat.id)
            bot.answer_callback_query(call.id, "Sent!")
        else:
            bot.answer_callback_query(call.id, r.get('error','Error'), show_alert=True)
        return
    if d in ['week', 'month']:
        price = PRICES.get(d, 15)
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("TON", callback_data=f"net_{d}_TON"),
            types.InlineKeyboardButton("TRC20", callback_data=f"net_{d}_TRC20"),
            types.InlineKeyboardButton("BEP20", callback_data=f"net_{d}_BEP20"),
            types.InlineKeyboardButton("ERC20", callback_data=f"net_{d}_ERC20")
        )
        kb.add(types.InlineKeyboardButton("Back", callback_data="back"), types.InlineKeyboardButton("Cancel", callback_data="cancel"))
        bot.edit_message_text(f"{d.upper()} - {price}$\n\nNetwork:", call.message.chat.id, call.message.message_id, reply_markup=kb)
        return
    if d == 'back':
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("FREE Trial", callback_data="trial"), types.InlineKeyboardButton("Week", callback_data="week"), types.InlineKeyboardButton("Month", callback_data="month"), types.InlineKeyboardButton("Cancel", callback_data="cancel"))
        bot.edit_message_text("Choose:", call.message.chat.id, call.message.message_id, reply_markup=kb)
        return
    if d.startswith('net_'):
        _, plan, net = d.split('_')
        wallet = WALLETS.get(net, 'Not set')
        price = PRICES.get(plan, 15)
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("VERIFY PAYMENT", callback_data=f"verify_{plan}_{net}"))
        kb.add(types.InlineKeyboardButton("Back", callback_data=plan))
        bot.edit_message_text(f"Send {price}$ USDT\n{net}: {wallet}\n\nClick VERIFY", call.message.chat.id, call.message.message_id, reply_markup=kb)
        return
    if d.startswith('verify_'):
        _, plan, net = d.split('_')
        price = PRICES.get(plan, 15)
        wallet = WALLETS.get(net, '')
        bot.edit_message_text("Checking...", call.message.chat.id, call.message.message_id)
        
        paid = check_payment(net, wallet, price)
        
        if paid is True:
            r = api('get_paid_key', type=plan, user_id=str(call.from_user.id))
            if r.get('key'):
                dur = '30d' if plan == 'month' else '7d'
                bot.send_message(call.message.chat.id, f"KEY: {r['key']}\n{dur}")
                send_apk(call.message.chat.id)
                bot.edit_message_text("Sent!", call.message.chat.id, call.message.message_id)
        elif paid is False:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("Check Again", callback_data=f"verify_{plan}_{net}"))
            bot.edit_message_text("Payment NOT found!\n\nSend exactly and try again.", call.message.chat.id, call.message.message_id, reply_markup=kb)
        else:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("GET KEY", callback_data=f"get_{plan}"))
            bot.edit_message_text(f"Manual verification for {net}\n\nClick GET KEY", call.message.chat.id, call.message.message_id, reply_markup=kb)
        return
    if d.startswith('get_'):
        plan = d.replace('get_', '')
        r = api('get_paid_key', type=plan, user_id=str(call.from_user.id))
        if r.get('key'):
            bot.send_message(call.message.chat.id, f"KEY: {r['key']}")
            send_apk(call.message.chat.id)
            bot.edit_message_text("Sent!", call.message.chat.id, call.message.message_id)
        return
    if d.startswith('adm_'):
        if str(call.from_user.id) != ADMIN_ID: return
        plan = d.replace('adm_', '')
        act = 'get_trial' if plan == 'trial' else 'get_paid_key'
        r = api(act, type=plan, user_id='admin')
        if r.get('key'):
            bot.send_message(call.message.chat.id, f"TEST: {r['key']}")
            send_apk(call.message.chat.id)
            bot.answer_callback_query(call.id, "Sent!")
        return

print("Ready!")
bot.polling(none_stop=True)