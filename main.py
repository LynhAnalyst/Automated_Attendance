# attendance_bot.py
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from geopy.distance import geodesic
from datetime import datetime
import csv

# Tọa độ địa lý của vị trí điểm danh mới (latitude, longitude)
OFFICE_COORDINATES = (x, y)  # Tọa độ

# Biến toàn cục để lưu trạng thái điểm danh
attendance_status = {
    "active": False,
    "users": set()  # Lưu ID người dùng đã điểm danh
}

# Hàm khởi động bot
async def start(update: Update, context):
    keyboard = [[KeyboardButton("Gửi vị trí", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    await update.message.reply_text("Chào mừng bạn! Hãy gửi vị trí để điểm danh.", reply_markup=reply_markup)

# Hàm xử lý lệnh điểm danh
async def handle_location(update: Update, context):
    if not attendance_status["active"]:
        await update.message.reply_text("Điểm danh đã kết thúc.")
        return

    user_id = update.message.from_user.id
    if user_id in [user_id for user_id, _ in attendance_status["users"]]:
        await update.message.reply_text("Bạn đã điểm danh rồi.")
        return

    user_location = (update.message.location.latitude, update.message.location.longitude)
    distance = geodesic(user_location, OFFICE_COORDINATES).meters

    if distance <= 100:  # Khoảng cách cho phép
        # Lấy tên người dùng
        user_name = update.message.from_user.username or "No Username"
        # Lưu thông tin điểm danh
        attendance_status["users"].add((user_id, user_name))
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await update.message.reply_text(f"Điểm danh thành công! Bạn đang cách {distance:.2f} mét từ vị trí điểm danh.")
    else:
        await update.message.reply_text(f"Điểm danh thất bại! Bạn đang cách {distance:.2f} mét từ vị trí điểm danh.")

# Hàm lưu kết quả điểm danh vào file CSV
def save_attendance_to_csv():
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"attendance_{today}.csv"
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['User ID', 'Username', 'Time'])
        
        for user_id, user_name in attendance_status["users"]:
            writer.writerow([user_id, user_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    print(f"Attendance data saved to {filename}")

# Hàm xử lý lệnh kết thúc điểm danh
async def end(update: Update, context):
    if update.message.from_user.id not in (7297390502, 6718346177):  # Thay đổi admin_id1, admin_id2 
        await update.message.reply_text("Bạn không có quyền thực hiện lệnh này.")
        return

    if attendance_status["active"]:
        # Kết thúc điểm danh
        attendance_status["active"] = False
        
        # Lưu kết quả vào file CSV
        save_attendance_to_csv()

        await update.message.reply_text("Điểm danh đã kết thúc và dữ liệu đã được lưu vào file CSV.")
    else:
        await update.message.reply_text("Điểm danh chưa được bắt đầu.")

# Hàm bắt đầu điểm danh
async def start_attendance(update: Update, context):
    if update.message.from_user.id not in (7297390502, 6718346177):  # Thay đổi admin_id1, admin_id2
        await update.message.reply_text("Bạn không có quyền thực hiện lệnh này.")
        return

    if not attendance_status["active"]:
        attendance_status["active"] = True
        attendance_status["users"].clear()
        
        # Gửi tin nhắn đến tất cả thành viên trong nhóm
        chat_id = update.message.chat_id
        message = "Điểm danh đã bắt đầu! Hãy gửi vị trí của bạn để điểm danh."
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.MARKDOWN)
        
        # Tạo nút gửi vị trí cho người dùng
        keyboard = [[KeyboardButton("Gửi vị trí", request_location=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        await context.bot.send_message(chat_id=chat_id, text="Chúng tôi đang chờ vị trí của bạn.", reply_markup=reply_markup)

        await update.message.reply_text("Điểm danh đã bắt đầu. Vui lòng gửi vị trí của bạn để điểm danh.")
    else:
        await update.message.reply_text("Điểm danh đã được bắt đầu rồi.")


if __name__ == "__main__":
    BOT_TOKEN = "TOKEN" 
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("start_attendance", start_attendance))
    app.add_handler(CommandHandler("end", end))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))

    print("Bot is running...")
    app.run_polling()
