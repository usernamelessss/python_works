import re

def run(bk):
    # EPUB临时工作目录
    print("EBOOK_ROOT:\n"+bk._w.ebook_root,end="\n\n")

    # 修改文件测试
    text = ""
    for mid,href in bk.text_iter():
        text = bk.readfile(mid)
        text = re.sub("<p>.*?</p>","<p>XXXXXXXXXXXXXXXXXXX</p>",text)
        bk.writefile(mid,text)

    # 删除manifest文件
    text = bk.readfile("Section0001.xhtml")
    bk.deletefile("Section0001.xhtml")

    # 添加文件测试
    bk.addfile("addedfile.xhtml","addedfile.xhtml",text)

    # 更新spine节点
    newspine = [(id,None) for id,href in bk.text_iter()]
    bk.setspine(newspine)

    # 删除非 manifest 文件
    for bkpath in bk.other_iter():
        if bkpath.lower().endswith(("mimetype",".opf",".xml")):
            continue
        bk.deleteotherfile(bkpath)

if __name__ == "__main__":
    from sigil_env import Ebook
    epub_src = "test.epub"
    bk = Ebook(epub_src)
    run(bk)
    bk.save_as("test_repack.epub")