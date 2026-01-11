
import os,re,sys
import zipfile
import random,uuid

from plugin_launchers.opf_parser import Opf_Parser
from plugin_launchers.wrapper import Wrapper
from plugin_launchers.bookcontainer import BookContainer
from plugin_launchers.inputcontainer import InputContainer
from plugin_launchers.outputcontainer import OutputContainer
from plugin_launchers.validationcontainer import ValidationContainer

SUPPORTED_SCRIPT_TYPES = ['input', 'output', 'edit', 'validation']

# Ebook负责EPUB的基本文件信息，创建临时工作目录和初始化 Opf_Parser、Wrapper 等类所需变量。
# 继承多个类仅仅是为了方便IDE智能提示，无实际作用，因为 __new__ 方法的存在，Ebook类最终不会赋予任何对象，
# 而是根据 plugin_type 返回 BookContainer、InputContainer、OutputContainer、ValidationContainer 之一的对象，
class Ebook(BookContainer, InputContainer, OutputContainer):
    def __init__(self, epub_src:str, plugin_type:str = "edit", plugin_dir:str = "", plugin_name:str = ""):
        '''
        epub_src\xa0\xa0\xa0\xa0\xa0\xa0\xa0\xa0源epub完整路径，必填。\n
        script_type\xa0\xa0\xa0\xa0\xa0插件类型，edit（默认） | input | output | validation 。\n
        plugin_dir\xa0\xa0\xa0\xa0\xa0\xa0插件位置，一般不填，除非需要。\n
        plugin_name\xa0\xa0插件名称，一般不填，除非需要。
        '''
        if plugin_type not in SUPPORTED_SCRIPT_TYPES:
            raise ValueError("Ebook: script type %s is not supported" % plugin_type)
        if os.path.exists(epub_src):
            epub_src = os.path.realpath(epub_src)
        else:
            raise FileNotFoundError("EPUB路径无效！")
        src_dir = os.path.dirname(epub_src)
        random_id = str(uuid.uuid5(uuid.NAMESPACE_DNS,str(random.randint(0, 10000))))
        self.ebook_root = ebook_root = os.path.join(src_dir,"__temp_workspace__","Ebook-%s"%(random_id))
        self.outdir = outdir = os.path.join(src_dir,"__temp_workspace__","Outdir-%s"%(random_id))
        self.epub = zipfile.ZipFile(epub_src,'a')
        opfbookpath = self.find_opf(self)
        opf_path = os.path.join(ebook_root, opfbookpath.replace("/", os.sep))
        self.create_temp_workspace(self)
        plugin_dir = ""
        plugin_name = ""
        op = None
        if os.path.exists(opf_path) and os.path.isfile(opf_path):
            op = Opf_Parser(opf_path, opfbookpath)
        self.rk = Wrapper(ebook_root, epub_src, outdir, op, plugin_dir, plugin_name)
    
    def __new__(cls, epub_src:str, plugin_type:str = "edit", plugin_dir:str = "", plugin_name:str = ""):
        cls.__init__(cls,epub_src,plugin_type,plugin_dir,plugin_name)
        # get the correct container
        if plugin_type == 'edit':
            bc = BookContainer(cls.rk)
        elif plugin_type == 'input':
            bc = InputContainer(cls.rk)
        elif plugin_type == 'validation':
            bc = ValidationContainer(cls.rk)
        elif plugin_type == 'output':
            bc = OutputContainer(cls.rk)
        else:
            raise ValueError("不支持的插件类型！")
        return bc
    
    def create_temp_workspace(self):
        if not os.path.exists(self.ebook_root):
            os.makedirs(self.ebook_root)
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)
        self.epub.extractall(self.ebook_root)
    
    def find_opf(self):
        #通过 container.xml 读取 opf 文件
        container_xml = self.epub.read('META-INF/container.xml').decode('utf-8')
        rf = re.match(r'<rootfile[^>]*full-path="(?i:(.*?\.opf))"',container_xml)
        if rf is not None:
            return rf.group(1)
        #通过路径首个 opf 读取 opf 文件
        for bkpath in self.epub.namelist():
            if bkpath.lower().endswith('.opf'):
                return bkpath
        raise FileNotFoundError('找不到opf文件！')
