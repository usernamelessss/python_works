
import sys
from os.path import join,dirname,realpath

curdir = dirname(__file__)
sys.path.append(curdir)
sys.path.append(realpath(join(curdir,"plugin_launchers")))

from .launcher import Ebook


__all__ = ["Ebook"]