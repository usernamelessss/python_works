import tkinter as tk
from tkinter import messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from fontTools.ttLib import TTFont


def get_font_info(file_path):
	"""优化后的字体解析逻辑，支持简繁英及多平台ID"""
	try:
		font = TTFont(file_path)
		name_record = font['name'].names

		names = {
			"en": {"family": "Unknown", "style": "Unknown"},
			"zh": {"family": "", "style": ""}
		}

		# 语言 ID 定义
		zh_lang_ids = [2052, 1028, 3076, 5124]  # 简、繁、港、澳

		for record in name_record:
			try:
				name_str = record.toUnicode()
			except:
				continue

			# 提取英文 (Windows 平台)
			if record.platformID == 3 and record.langID == 1033:
				if record.nameID in [1, 16]:
					names["en"]["family"] = name_str
				elif record.nameID == 2:
					names["en"]["style"] = name_str

			# 提取中文 (Windows 平台)
			if record.platformID == 3 and record.langID in zh_lang_ids:
				if record.nameID in [1, 16]:
					names["zh"]["family"] = name_str

			# 兼容 Mac 平台中文
			elif record.platformID == 1 and record.langID in [19, 25]:
				if record.nameID in [1, 16]:
					names["zh"]["family"] = name_str

		zh_family = names["zh"]["family"] if names["zh"]["family"] else "（该字体未内置中文名称）"

		return {
			"en_family": names["en"]["family"],
			"zh_family": zh_family,
			"style": names["en"]["style"]
		}
	except Exception as e:
		return f"解析失败: {str(e)}"


def center_window(window, width, height):
	"""将窗口放置在屏幕中央"""
	screen_width = window.winfo_screenwidth()
	screen_height = window.winfo_screenheight()

	x = int((screen_width / 2) - (width / 2))
	y = int((screen_height / 2) - (height / 2))

	window.geometry(f"{width}x{height}+{x}+{y}")


def drop(event):
	file_path = event.data.strip('{}')
	if file_path.lower().endswith(('.ttf', '.otf', '.ttc')):
		res = get_font_info(file_path)
		result_text.config(state=tk.NORMAL)
		result_text.delete(1.0, tk.END)

		if isinstance(res, dict):
			content = (
				f"【文件路径】: {file_path}\n"
				f"{'=' * 50}\n"
				f"英文家族名称:  {res['en_family']}\n"
				f"中文家族名称:  {res['zh_family']}\n"
				f"样式/子族名:   {res['style']}\n"
				f"{'=' * 50}\n"
				f"提示：可直接拖动鼠标选中上方文字复制。"
			)
			result_text.insert(tk.END, content)
		else:
			result_text.insert(tk.END, res)
	else:
		messagebox.showwarning("格式错误", "请拖入 .ttf, .otf 或 .ttc 文件")


# 初始化
root = TkinterDnD.Tk()
root.title("字体信息提取工具")

# 设置窗口大小并居中
win_w, win_h = 650, 450
center_window(root, win_w, win_h)

# 界面元素
label_hint = tk.Label(root, text="请将字体文件拖拽到下方区域", pady=15, font=("微软雅黑", 10, "bold"))
label_hint.pack()

result_text = tk.Text(root, wrap=tk.WORD, width=80, height=18, bg="#fbfbfb", padx=15, pady=15, font=("Consolas", 10))
result_text.pack(padx=20, pady=10)
result_text.insert(tk.END, "等待拖入文件...")

# 注册拖拽
result_text.drop_target_register(DND_FILES)
result_text.dnd_bind('<<Drop>>', drop)

root.mainloop()
