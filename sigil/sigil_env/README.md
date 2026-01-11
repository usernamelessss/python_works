# Sigil插件环境模拟包
模拟Sigil插件环境的，让Sigil插件摆脱 Sigil 平台，在其他平台的 Python 环境下运行。
Sigil启动插件时，会根据插件类型将 epub 分别打包为 BookContainer 对象、InputContainer 对象、OutputContainer 对象 或 ValidationContainer 对象。即 插件入口 run(bk) 的唯一参数 bk 对象。

此包的功能正是将 epub 打包为 BookContainer 等四种类型之一的对象，以供插件调试使用。

## **使用方法：**
### **导入包**
```python
from sigil_env import Ebook
```

### **示例**
```python
# 插件入口
def run(bk):
    print(list(bk.text_iter()))
    return 0

# sigil_env 包建议在 plugin.py 的 __main__ 入口下导入与使用，
# 该入口下可保留调试代码，不需担心调试代码与实际Sigil环境的差异。
# 因为 Sigil 插件正式运行时只进入 run 入口，不会经过 __main__ 入口。
if __name__ == "__main__":
    # 导入包
    from sigil_env import Ebook
    # Epub 源路径
    epub_src = "test.epub"
    # 打包对象
    bk = Ebook(epub_src)
    # 插件运行
    run(bk)
    # epub 另存为
    bk.save_as("test_repack.epub")
```
### **打包 BookContainer 对象**
```python
# 默认打包类型为 BookContainer
bk = EBook(epub_src)
# 或
bk = EBook(epub_src, plugin_type="edit")
```

### **打包 InputContainer 对象**
```python
bk = EBook(epub_src, plugin_type="input")
```
### **打包 OutputContainer 对象**
```python
bk = EBook(epub_src, plugin_type="output")
```
### **打包 ValidationContainer 对象**
```python
bk = EBook(epub_src, plugin_type="validation")
```
### **重构 EPUB 为 Sigil 标准格式**
```python
bk.standardize_epub()
```
注意： `standardize_epub` 方法是 sigil_env 包独有，实际插件环境的 bk 对象并不存在该方法，因此该方法建议只在 `__main__` 入口下调用。

### **另存为**
调用 `bk.save_as(filepath)` 可将 bk 对象导出为 Epub，一般在插件程序完成后调用功能以生成处理过的EPUB。<br>
仅限 `BookContainer`、`InputContainer` 的对象可调用 `save_as` ，其他两个类不需要也不能调用 `save_as` 方法。 <br>
```python
bk.save_as() # 如果不指定路径，默认生成在源EPUB同级目录的 "OUTPUT/[同名].epub"
# 或
bk.save_as("test_repack.epub") # 指定生成路径
```
需要注意的是，`save_as` 方法是 sigil_env 包独有，实际插件环境的 bk 对象并不存在该方法。因此该方法建议只在 `__main__` 入口下调用。

### **导入 sigil_bs4 库**
`sigil_bs4` 库是Sigil插件环境自带的一个库，在导入 sigil_env 后也可以导入该库。不过一般等到 `__main__` 入口再导入 sigil_env 有点迟，如果需要 `sigil_bs4` ，建议在文件开头导入 sigil_env。

例如：
```python
# 在文件开头即导入 sigil_env 包，可保证 sigil_bs4 的导入正常
from sigil_env import Ebook
from sigil_bs4 import BeautifulSoup

def run(bk):
    '''your plugin entry'''
    return 0
    
if __name__ == "__main__":
    epub_src = "test.epub"
    bk = Ebook(epub_src)
    run(bk)
```
### **临时目录**
Sigil插件环境模拟包运行时，会在源epub的相同目录下产生一个名为 `__temp_workspace__` 的目录，临时存放 epub 解压内容。如果插件完全正常运行，则运行结束后该临时目录会自动清除，如果插件异常退出，则可能需要手动清除该目录。