import ctypes
import sqlite3
import tkinter as tk
from tkinter import ttk
import datetime
from tkinter import messagebox

def adjust_treeview_column_widths(tree, min_padding=50):
    import tkinter as tk
    import tkinter.font as tkFont

    columns = tree["columns"]
    font = tkFont.Font(font=("Microsoft YaHei", 11))

    for col in columns:
        max_width = font.measure(col)

        for item in tree.get_children():
            text = str(tree.set(item, col))
            width = font.measure(text)
            if width > max_width:
                max_width = width

        tree.column(col, width=max_width + min_padding)

def book_query():
    win = tk.Toplevel()
    win.title("查询书籍状态")
    win.geometry("1200x600")

    ttk.Label(win, text="输入书名或作者或ISBN", font=("Microsoft YaHei", 14)).pack(pady=30)

    # 新建一行的 Frame
    input_frame = tk.Frame(win)
    input_frame.pack(pady=10)

    entry = ttk.Entry(input_frame, width=50)
    entry.pack(side=tk.LEFT, padx=5)

    button = ttk.Button(input_frame, text="查询", 
                        command=lambda: search_books(entry.get(), tree))
    button.pack(side=tk.LEFT, padx=5)

    # TreeView 在下面
    columns = ("ID", "书名", "作者", "出版社", "年份", "ISBN", "类别", "库存量")
    tree = ttk.Treeview(win, columns=columns, show="headings")

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)

    tree.pack(fill=tk.BOTH, expand=True, pady=20)

def search_books(query, tree):
    """根据查询条件搜索书籍并更新树视图"""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT books.id, books.title, books.author, books.publisher, books.year,
               books.isbn, categories.name AS category, books.copies
        FROM books
        LEFT JOIN categories ON books.category_id = categories.id
        WHERE books.title LIKE ? OR books.author LIKE ? OR books.isbn LIKE ?
    """, (f"%{query}%", f"%{query}%", f"%{query}%"))

    results = cursor.fetchall()
    conn.close()

    # 清空现有数据
    for item in tree.get_children():
        tree.delete(item)

    # 插入新数据
    for row in results:
        tree.insert("", tk.END, values=row)
    
    adjust_treeview_column_widths(tree)

def borrow_query():
    win = tk.Toplevel()
    win.title("查询借阅记录")
    win.geometry("800x400")

    ttk.Label(win, text="输入读者ID或书名", font=("Microsoft YaHei", 14)).pack(pady=30)

    # 新建一行的 Frame
    input_frame = tk.Frame(win)
    input_frame.pack(pady=10)

    entry = ttk.Entry(input_frame, width=50)
    entry.pack(side=tk.LEFT, padx=5)

    button = ttk.Button(input_frame, text="查询", 
                        command=lambda: search_borrows(entry.get(), tree))
    button.pack(side=tk.LEFT, padx=5)

    # TreeView 在下面
    columns = ("借阅ID", "读者ID", "书名", "副本ID", "借阅日期", "归还日期", "归还状态")
    tree = ttk.Treeview(win, columns=columns, show="headings")

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)

    tree.pack(fill=tk.BOTH, expand=True, pady=20)

def search_borrows(query, tree):
    """根据查询条件搜索借阅记录并更新树视图"""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT borrows.id, borrows.user_id, books.title, borrows.copy_id,
               borrows.borrow_time, borrows.return_date, borrows.returned
        FROM borrows
        LEFT JOIN copies ON borrows.copy_id = copies.id
        LEFT JOIN books  ON copies.book_id = books.id
        WHERE borrows.user_id LIKE ? OR books.title LIKE ?
    """, (f"%{query}%", f"%{query}%"))

    results = cursor.fetchall()
    conn.close()

    # 清空现有数据
    for item in tree.get_children():
        tree.delete(item)

    # 插入新数据
    for row in results:
        tree.insert("", tk.END, values=row)

    adjust_treeview_column_widths(tree)

def open_operation_window(number):
    """打开一个新的操作窗口"""
    win = tk.Toplevel()
    win.title(f"操作窗口 {number}")
    win.geometry("300x150")

    ttk.Label(win, text=f"这里是操作窗口 {number}", font=("Arial", 14)).pack(pady=30)
    ttk.Button(win, text="关闭", command=win.destroy).pack()

def book_borrow():
    win = tk.Toplevel()
    win.title("借书")
    win.geometry("600x400")

    ttk.Label(win, text="请输入借书信息", font=("Microsoft YaHei", 16)).pack(pady=25)

    # ====== 表单区域（用 grid 更好看） ======
    form = tk.Frame(win)
    form.pack(pady=20)

    # 第一行：读者 ID
    ttk.Label(form, text="读者ID：", font=("Microsoft YaHei", 12)).grid(row=0, column=0, padx=10, pady=10, sticky="e")
    entry_user_id = ttk.Entry(form, width=35)
    entry_user_id.grid(row=0, column=1, padx=10, pady=10)

    # 第二行：副本 ID
    ttk.Label(form, text="副本ID：", font=("Microsoft YaHei", 12)).grid(row=1, column=0, padx=10, pady=10, sticky="e")
    entry_book_id = ttk.Entry(form, width=35)
    entry_book_id.grid(row=1, column=1, padx=10, pady=10)

    # 第三行：按钮（居中）
    button = ttk.Button(form, text="借书",
                        command=lambda: execute_borrow(entry_user_id.get(), entry_book_id.get()))
    button.grid(row=2, column=0, columnspan=2, pady=20)

def execute_borrow(user_id, book_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # 检查副本是否可借
    cursor.execute("SELECT status, borrowable FROM copies WHERE id=?", (book_id,))
    result01 = cursor.fetchone()
    cursor.execute("SELECT maxborrow, borrowed_count FROM users WHERE id=?", (user_id,))
    result02 = cursor.fetchone()

    result= result01 and (result02[1] < result02[0])

    if not result:
        messagebox.showerror("错误", "副本ID不存在！")
    else:
        status, borrowable = result01
        if status != 'available' or borrowable == 0:
            messagebox.showerror("错误", "该副本不可借！")
        else:
            # 执行借书操作
            cursor.execute("""
                INSERT INTO borrows (user_id, copy_id)
                VALUES (?, ?)
            """, (user_id, book_id))

            # 更新副本状态
            cursor.execute("""
                UPDATE copies
                SET status='borrowed'
                WHERE id=?
            """, (book_id,))
            # 更新用户已借书数量
            cursor.execute("""
                UPDATE users
                SET borrowed_count = borrowed_count + 1
                WHERE id=?
            """, (user_id,))

            conn.commit()
            messagebox.showinfo("成功", "借书成功！")

    conn.close()



def update_clock(label):
    """实时更新时钟"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    label.config(text=f"当前时间：{now}")
    label.after(1000, update_clock, label)


def create_main_window(username):
    root = tk.Tk()
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
    root.tk.call('tk',"scaling", ScaleFactor/75)
    style = ttk.Style()
    style.configure("Treeview", 
                rowheight = int(28 * float(ScaleFactor) / 96),
                font=("Microsoft YaHei", 9))
    root.title("主界面")
    root.geometry("400x600")

    # 登录用户显示
    user_label = ttk.Label(root, text=f"当前登录用户：{username}", font=("Arial", 14))
    user_label.pack(pady=10)

    bookcount = 0
    conn= sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM books")
    bookcount = cursor.fetchone()[0]


    user_label = ttk.Label(root, text=f"当前系统共有书籍数量：{bookcount}", font=("Arial", 12))
    user_label.pack(pady=10)
    conn.close()

    # 时钟
    clock_label = ttk.Label(root, text="", font=("Arial", 12))
    clock_label.pack(pady=10)
    update_clock(clock_label)

    # 操作按钮
    button_frame = ttk.Frame(root)
    button_frame.pack(pady=40)

    ttk.Button(button_frame, text="查询书籍状态", width=20,
               command=lambda: book_query()).pack(pady=5)
    ttk.Button(button_frame, text="查询借阅记录", width=20,
               command=lambda: borrow_query()).pack(pady=5)
    ttk.Button(button_frame, text="借书", width=20,
               command=lambda: book_borrow()).pack(pady=5)
    ttk.Button(button_frame, text="还书", width=20,
               command=lambda: open_operation_window(4)).pack(pady=5)
    ttk.Button(button_frame, text="新增书籍", width=20,
               command=lambda: open_operation_window(5)).pack(pady=5)
    ttk.Button(button_frame, text="书籍报损", width=20,
               command=lambda: open_operation_window(9)).pack(pady=5)
    ttk.Button(button_frame, text="读者管理", width=20,
               command=lambda: open_operation_window(6)).pack(pady=5)
    ttk.Button(button_frame, text="退出登录", width=20,
               command=lambda: open_operation_window(7)).pack(pady=5)
    root.mainloop()


# 示例：假设登录用户名是 admin

if __name__ == "__main__":
    username = "debug_admin"
    create_main_window(username)