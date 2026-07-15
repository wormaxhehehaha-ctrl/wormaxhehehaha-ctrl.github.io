import json
import telebot
from telebot import types
import requests
import time
import threading

BOT_TOKEN = '8886583166:AAEOOLPEX_sDW6ivAwpvesHjGbtDjQa4mi8'

with open('bot_settings.json', 'r') as f:
    settings = json.load(f)

ADMIN_ID = str(settings['admin_telegram_id'])
API_URL = 'http://keycodm.atwebpages.com/bot_api.php'
WALLETS = settings['usdt_wallets']
PRICES = settings['prices']
APK_URL = settings.get('apk_url', 'https://raw.githubusercontent.com/wormaxhehehaha-ctrl/Idk/main/app.apk')

ETHERSCAN_KEY = 'ZY83K9SN25FUCQE77EVMVVRZR1I4VCH96T'
TON_API_KEY = '157dd7ed7dcab4c0dc6d736f7a0c873f4b166b78291fb95892c9b240a7b9167b'

# Kill old sessions
requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook', timeout=5)
time.sleep(1)

bot = telebot.TeleBot(BOT_TOKEN)
print("🤖 Bot starting...")

# Download APK to memory
APK_DATA = None
try:
    resp = requests.get(APK_URL, timeout=30)
    if resp.status_code == 200:
        APK_DATA = resp.content
        print(f"APK loaded: {len(APK_DATA)} bytes")
except:
    print("APK download failed, will send link")

# ========== API ==========

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
            bot.send_document(chat_id, APK_DATA, visible_file_name="CODM_ELITE.apk", caption="📱 CODM ELITE")
            return
        except:
            pass
    bot.send_message(chat_id, f"📥 Download APK:\n{APK_URL}")

# ========== PAYMENT CHECKS ==========

def check_trc20(wallet, amount):
    try:
        url = f"https://api.trongrid.io/v1/accounts/{wallet}/transactions/trc20?limit=10&only_confirmed=true"
        data = requests.get(url, timeout=10).json()
        for tx in data.get('data', []):
            if time.time() - tx.get('block_timestamp', 0)/1000 < 600:
                if tx.get('to', '').lower() == wallet.lower():
                    if int(tx.get('value', 0))/1000000 >= amount * 0.95:
                        return True
        return False
    except:
        return False

def check_bep20(wallet, amount):
    try:
        url = f"https://api.bscscan.com/api?module=account&action=tokentx&address={wallet}&sort=desc&apikey={ETHERSCAN_KEY}"
        data = requests.get(url, timeout=10).json()
        if data.get('status') == '1':
            for tx in data.get('result', []):
                if time.time() - int(tx.get('timeStamp', 0)) < 600:
                    if tx.get('to', '').lower() == wallet.lower():
                        if int(tx.get('value', 0))/1e18 >= amount * 0.95:
                            return True
        return False
    except:
        return False

def check_erc20(wallet, amount):
    try:
        url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={wallet}&sort=desc&apikey={ETHERSCAN_KEY}"
        data = requests.get(url, timeout=10).json()
        if data.get('status') == '1':
            for tx in data.get('result', []):
                if time.time() - int(tx.get('timeStamp', 0)) < 600:
                    if tx.get('to', '').lower() == wallet.lower():
                        if int(tx.get('value', 0))/1e18 >= amount * 0.95:
                            return True
        return False
    except:
        return False

def check_ton(wallet, amount):
    try:
        headers = {'X-API-Key': TON_API_KEY}
        url = f"https://toncenter.com/api/v2/getTransactions?address={wallet}&limit=10"
        data = requests.get(url, headers=headers, timeout=10).json()
        if data.get('ok') and 'result' in data:
            for tx in data['result']:
                if time.time() - tx.get('utime', 0) < 600:
                    if 'in_msg' in tx and 'value' in tx['in_msg']:
                        value = int(tx['in_msg']['value']) / 1e9
                        if value >= amount * 0.95:
                            return True
        return False
    except:
        return False

def check_payment(network, wallet, amount):
    if network == "TRC20":
        return check_trc20(wallet, amount)
    elif network == "BEP20":
        return check_bep20(wallet, amount)
    elif network == "ERC20":
        return check_erc20(wallet, amount)
    elif network == "TON":
        return check_ton(wallet, amount)
    return False

# ========== COMMANDS ==========

@bot.message_handler(commands=['start'])
def start(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("FREE Trial", "Buy Plan", "Profile", "Support")
    bot.send_message(msg.chat.id, "⚡ CODM ELITE SHOP\n@CODM_KEYSHOP_BOT", reply_markup=kb)

@bot.message_handler(commands=['buy'])
def buy(msg):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("FREE Trial (1 time)", callback_data="trial"),
        types.InlineKeyboardButton("Week - 15$ USDT", callback_data="week"),
        types.InlineKeyboardButton("Month - 30$ USDT", callback_data="month"),
        types.InlineKeyboardButton("Cancel", callback_data="cancel")
    )
    bot.send_message(msg.chat.id, "💳 Choose plan:", reply_markup=kb)

@bot.message_handler(commands=['profile'])
def profile(msg):
    d = api('profile', user_id=str(msg.from_user.id))
    t = "USED" if d.get('has_trial') else "AVAILABLE"
    bot.send_message(msg.chat.id, f"👤 Profile\nID: {msg.from_user.id}\nTrial: {t}")

@bot.message_handler(commands=['support'])
def support(msg):
    bot.send_message(msg.chat.id, "💬 Support: @idkidk1010")

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
    bot.send_message(msg.chat.id, "🧪 ADMIN TEST", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text and "Trial" in m.text)
def t_trial(msg):
    d = api('get_trial', user_id=str(msg.from_user.id))
    if d.get('key'):
        bot.send_message(msg.chat.id, f"✅ KEY: {d['key']}\n⏰ 6h\n📱 1 device")
        send_apk(msg.chat.id)
    else:
        bot.send_message(msg.chat.id, d.get('error', 'Error'))

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
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        return
    
    if d == 'trial':
        r = api('get_trial', user_id=str(call.from_user.id))
        if r.get('key'):
            bot.send_message(call.message.chat.id, f"✅ KEY: {r['key']}\n⏰ 6h\n📱 1 device")
            send_apk(call.message.chat.id)
            bot.answer_callback_query(call.id, "Sent!")
        else:
            bot.answer_callback_query(call.id, r.get('error', 'Error'), show_alert=True)
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
        bot.edit_message_text(f"{d.upper()} - {price}$ USDT\n\nChoose network:", call.message.chat.id, call.message.message_id, reply_markup=kb)
        return
    
    if d == 'back':
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("FREE Trial", callback_data="trial"),
            types.InlineKeyboardButton("Week - 15$", callback_data="week"),
            types.InlineKeyboardButton("Month - 30$", callback_data="month"),
            types.InlineKeyboardButton("Cancel", callback_data="cancel")
        )
        bot.edit_message_text("💳 Choose plan:", call.message.chat.id, call.message.message_id, reply_markup=kb)
        return
    
    if d.startswith('net_'):
        _, plan, net = d.split('_')
        price = PRICES.get(plan, 15)
        wallet = WALLETS.get(net, 'Not set')
        
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔍 VERIFY PAYMENT", callback_data=f"verify_{plan}_{net}"))
        kb.add(types.InlineKeyboardButton("Back", callback_data=plan))
        kb.add(types.InlineKeyboardButton("Cancel", callback_data="cancel"))
        
        bot.edit_message_text(
            f"💰 Send {price}$ USDT\n\n📡 Network: {net}\n🔑 Wallet:\n{wallet}\n\n⚠️ Send ONLY USDT!\n✅ Click VERIFY after sending",
            call.message.chat.id, call.message.message_id, reply_markup=kb)
        return
    
    if d.startswith('verify_'):
        _, plan, net = d.split('_')
        price = PRICES.get(plan, 15)
        wallet = WALLETS.get(net, '')
        user_id = str(call.from_user.id)
        
        bot.edit_message_text(f"🔍 Checking {net} blockchain...", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Checking...")
        
        paid = False
        for i in range(3):
            time.sleep(3)
            paid = check_payment(net, wallet, price)
            if paid:
                break
        
        if paid:
            r = api('get_paid_key', type=plan, user_id=user_id)
            if r.get('key'):
                dur = '30 days' if plan == 'month' else '7 days'
                dev = '5 devices' if plan == 'month' else '1 device'
                bot.send_message(call.message.chat.id, f"✅ PAYMENT CONFIRMED!\n\n🔑 KEY: {r['key']}\n📅 {dur}\n📱 {dev}")
                send_apk(call.message.chat.id)
                bot.edit_message_text("✅ Sent! Check messages.", call.message.chat.id, call.message.message_id)
                try:
                    bot.send_message(ADMIN_ID, f"💰 SALE! {plan} | {net} | {price}$")
                except:
                    pass
            else:
                bot.edit_message_text(f"❌ {r.get('error', 'No keys')}", call.message.chat.id, call.message.message_id)
        else:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔄 Check Again", callback_data=f"verify_{plan}_{net}"))
            kb.add(types.InlineKeyboardButton("📩 Contact Admin", url="https://t.me/idkidk1010"))
            
            bot.edit_message_text(
                f"❌ Payment NOT detected!\n\n📡 {net} | 💰 {price}$\n\nCheck and try again or contact admin",
                call.message.chat.id, call.message.message_id, reply_markup=kb)
        return
    
    if d.startswith('adm_'):
        if str(call.from_user.id) != ADMIN_ID:
            return
        plan = d.replace('adm_', '')
        act = 'get_trial' if plan == 'trial' else 'get_paid_key'
        r = api(act, type=plan, user_id='admin')
        if r.get('key'):
            bot.send_message(call.message.chat.id, f"✅ TEST: {r['key']}")
            send_apk(call.message.chat.id)
            bot.answer_callback_query(call.id, "Sent!")
        return

# ========== SELF-PING ==========

def self_ping():
    while True:
        time.sleep(300)
        try:
            requests.get('https://codmelitebot.onrender.com', timeout=10)
        except:
            pass

threading.Thread(target=self_ping, daemon=True).start()

print("✅ Bot ready with self-ping!")
bot.polling(none_stop=True)