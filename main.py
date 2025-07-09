import telebot
import json
import os

TOKEN = '7521283553:AAGLZkgcRdEyOaGeKOPrWa2glfUEetjNv_8'  # <-- bu yerga o'z Telegram bot tokeningizni yozing
bot = telebot.TeleBot(TOKEN)

DATA_FILE = 'data.json'

# --- ADMINLAR RO'YXATI (shu yerga admin ID yozing) ---
ADMIN_IDS = [5101972399]  # <--- BU YERGA O'Z TELEGRAM ID’NGIZNI YOZING


# --- JSON yuklash va saqlash ---
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({"tests": {}, "results": {}}, f)
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


# --- ADMIN TEKSHIRUV ---
def is_admin(user_id):
    return user_id in ADMIN_IDS


# --- JAVOB FORMATINI PARSE QILISH ---
def parse_answers(answer_str):
    parsed = {}
    i = 0
    while i < len(answer_str):
        if i + 1 < len(answer_str) and answer_str[i].isdigit():
            q_num = answer_str[i]
            answer = answer_str[i + 1].lower()
            parsed[q_num] = answer
            i += 2
        else:
            i += 1
    return parsed


# --- ADMIN: TEST QO‘SHISH ---
@bot.message_handler(func=lambda msg: is_admin(msg.from_user.id) and "*" in msg.text)
def add_test(message):
    data = load_data()
    try:
        test_code, answers_raw = message.text.split("*")
        parsed_answers = parse_answers(answers_raw)
        data["tests"][test_code] = {"answers": parsed_answers}
        save_data(data)
        bot.reply_to(message, f"✅ Test {test_code} muvaffaqiyatli qo‘shildi.")
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")


# --- ADMIN: TESTNI O‘CHIRISH + STATISTIKA ---
@bot.message_handler(commands=['delete'])
def delete_test(message):
    data = load_data()
    user_id = message.from_user.id
    if not is_admin(user_id):
        return bot.reply_to(message, "❌ Sizda bu amalni bajarishga ruxsat yo‘q.")
    
    try:
        _, test_code = message.text.split()
        if test_code not in data["tests"]:
            return bot.reply_to(message, "❌ Bunday test topilmadi.")
        
        # Statistika chiqarish
        results = data.get("results", {}).get(test_code, [])
        if not results:
            bot.send_message(message.chat.id, f"ℹ️ Test {test_code} hech kim tomonidan yechilmagan.")
        else:
            total = len(results)
            stats = f"📊 Test: {test_code}\n👥 Topshirganlar soni: {total}\n\n"
            sum_percent = 0
            for i, r in enumerate(results, 1):
                percent = round((r['correct'] / r['total']) * 100)
                stats += f"{i}. {r['name']} – {r['correct']}/{r['total']} ({percent}%)\n"
                sum_percent += percent
            avg = round(sum_percent / total)
            stats += f"\n📉 O‘rtacha natija: {avg}%"
            bot.send_message(message.chat.id, stats)

        # Testni o‘chirish
        data["tests"].pop(test_code)
        data["results"].pop(test_code, None)
        save_data(data)
        bot.send_message(message.chat.id, f"🗑 Test {test_code} o‘chirildi.")
    except:
        bot.reply_to(message, "❌ To‘g‘ri format: /delete 555")


# --- FOYDALANUVCHI: TEST TOPSHIRISH ---
@bot.message_handler(func=lambda msg: "*" in msg.text)
def check_test(message):
    data = load_data()
    try:
        test_code, user_answers_raw = message.text.split("*")
        user_id = str(message.from_user.id)
        name = message.from_user.first_name

        if test_code not in data["tests"]:
            return bot.reply_to(message, "❌ Bunday test topilmadi.")

        # Oldin topshirganmi?
        if any(r['user_id'] == user_id for r in data.get("results", {}).get(test_code, [])):
            return bot.reply_to(message, "⛔ Siz bu testni allaqachon topshirgansiz.")

        correct_answers = data["tests"][test_code]["answers"]
        user_answers = parse_answers(user_answers_raw)

        total = len(correct_answers)
        correct = sum(1 for q, a in user_answers.items() if correct_answers.get(q) == a)

        percent = round((correct / total) * 100)

        # Saqlash
        result = {
            "user_id": user_id,
            "name": name,
            "correct": correct,
            "total": total
        }
        data.setdefault("results", {}).setdefault(test_code, []).append(result)
        save_data(data)

        bot.reply_to(message, f"✅ Natija: {correct}/{total} ({percent}%)")
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")


# --- /start buyrug‘i ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Test botga xush kelibsiz!\nTest topshirish uchun: 555*1a2b3c\nAdminlar test qo‘shishi mumkin.")


# --- Botni ishga tushirish ---
print("🤖 Bot ishga tushdi...")
bot.infinity_polling()
