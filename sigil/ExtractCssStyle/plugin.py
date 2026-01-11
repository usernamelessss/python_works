# -*- coding:utf-8 -*-
import re

from sigil_env import Ebook

import tkinter as tk


def css_parse(css_text):
    css_obj = {}
    rule = css_text.split('\r\n')

    for item in rule:
        value = item.strip()
        flag = value.find("{")
        if flag > -1:
            value = value.split('{')
            print(value[0].strip())
        # break
        # parts = value.split("{");
        # selector = parts[0].strip();

        # properties = parts[1].strip().slice(0, -1).strip(";");

        # css_obj[selector] = {};
        # break


def run(bk):
    css_list = bk.css_iter()
    for css in css_list:
        manifest_id = css[0]
        if manifest_id == 'main.css':
            css_string = bk.readfile(manifest_id)
            css_parse(css_string)


def getEntry():
    string = entry.get()  # 获取Entry的内容
    print(string)


def clear():
    entry.delete(0, 'end')  # 删除清空Entry控件的内容

    font = ('微软雅黑', 12)
    root = tk.Tk()
    root.geometry('250x150')  # 设定窗口的大小

    label = tk.Label(root, text='请输入姓名', font=font, height=2)
    label.pack()
    entry = tk.Entry(root, font=font)
    entry.pack()
    button01 = tk.Button(root, text='获取信息', font=font, command=getEntry)
    button01.pack()
    button02 = tk.Button(root, text='清空', font=font, command=clear)
    button02.pack()

    root.mainloop()


def input():
    font = ('微软雅黑', 12)

    root = tk.Tk()
    root.geometry('250x150')  # 设定窗口的大小

    label = tk.Label(root, text='请输入姓名', font=font, height=2)
    label.pack()

    entry = tk.Entry(root, font=font)
    entry.pack()

    button = tk.Button(root, text='测试', font=font)
    button.pack()

    root.mainloop()


if __name__ == '__main__':
    # epub_path = r'demo.epub'
    # bk = Ebook(epub_path)
    # print(dir(bk))
    # run(bk)

    input()
