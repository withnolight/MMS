import sqlite3
import smtplib
from datetime import datetime, timedelta
import schedule
import time
from email.mime.text import MIMEText
from email.header import Header

DB = "database.db"


#########################
#   发送 Email 函数     #
#########################
SMTP_SERVER = "smtp.gmail.com"     # 修改为你的 SMTP 服务
SMTP_PORT = 587                    # TLS
SMTP_EMAIL = "your_email@gmail.com"
SMTP_PASSWORD = "your_email_app_password"  # 邮箱专用 APP 密码

def send_email(to, subject, content):
    msg = MIMEText(content, "plain", "utf-8")
    msg["From"] = SMTP_EMAIL
    msg["To"] = to
    msg["Subject"] = Header(subject, "utf-8")

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to, msg.as_string())
        server.quit()
        print(f"📧 已发送提醒到 {to}")
    except Exception as e:
        print(f"发送邮件失败: {e}")


#############################
#   4:00AM 建立索引任务     #
#############################
def create_indexes():
    print("⏳ 建立高频访问索引...")

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # 索引示例：按需修改
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_books_title ON books(title)",
        "CREATE INDEX IF NOT EXISTS idx_borrows_user ON borrows(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_borrows_copy ON borrows(copy_id)",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
    ]

    for sql in indexes:
        cursor.execute(sql)

    conn.commit()
    conn.close()
    print("✅ 索引任务完成")


#############################################
#   8:00AM 发送超期未还邮件提醒任务          #
#############################################
def send_overdue_emails():
    print("⏳ 检查并发送超期借阅邮件...")

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    # 超过 30 天且未归还 borrowed.returned = 0
    cursor.execute("""
        SELECT borrows.user_id, users.email, borrows.borrow_time, copies.book_id, books.title
        FROM borrows
        JOIN users ON borrows.user_id = users.id
        JOIN copies ON borrows.copy_id = copies.id
        JOIN books ON copies.book_id = books.id
        WHERE borrows.returned = 0
          AND DATE(borrows.borrow_time) <= DATE('now', '-30 days');
    """)

    overdue_records = cursor.fetchall()
    conn.close()

    for user_id, email, borrow_time, book_id, title in overdue_records:
        if not email:
            continue

        content = (
            f"您好，您的借阅已超期：\n\n"
            f"书名：{title}\n"
            f"借阅时间：{borrow_time}\n"
            f"当前已超过 30 天，请尽快归还。\n\n"
            "图书馆管理系统自动提醒"
        )
        send_email(email, "图书超期未还提醒", content)

    print("✅ 超期提醒已发送完成")


###################
#   注册定时任务   #
###################
schedule.every().day.at("04:00").do(create_indexes)
schedule.every().day.at("08:00").do(send_overdue_emails)

print("📌 定时任务已启动...")
print("  每天 04:00 → 构建索引")
print("  每天 08:00 → 发送超期邮件")
print("保持脚本运行即可。")

# 持续运行（最好用 screen / systemd 托管）
while True:
    schedule.run_pending()
    time.sleep(1)
