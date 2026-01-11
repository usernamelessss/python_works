#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Copyright (c) 2014-2022 Kevin B. Hendricks and Doug Massay
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of
# conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list
# of conditions and the following disclaimer in the documentation and/or other materials
# provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY
# WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from collections import OrderedDict
import sys
import os
import re
from hrefutils import urldecodepart, urlencodepart
from hrefutils import buildBookPath, startingDir, buildRelativePath
from hrefutils import ext_mime_map, mime_group_map
import unicodedata
import shutil
import zipfile

def _utf8str(p):
    if p is None:
        return None
    if isinstance(p, bytes):
        return p
    return p.encode('utf-8', errors='replace')

def _unicodestr(p):
    if p is None:
        return None
    if isinstance(p, str):
        return p
    return p.decode('utf-8', errors='replace')

_launcher_version = 20230315

_PKG_VER = re.compile(r'''<\s*package[^>]*version\s*=\s*["']([^'"]*)['"][^>]*>''', re.IGNORECASE)

# Wrapper Class is used to peform record keeping for Sigil.  It keeps track of modified,
# added, and deleted files while providing some degree of protection against files under
# Sigil's control from being directly manipulated.
# Uses "write-on-modify" and so removes the need for wholesale copying of files

_guide_types = ['cover', 'title-page', 'toc', 'index', 'glossary', 'acknowledgements',
                'bibliography', 'colophon', 'copyright-page', 'dedication',
                'epigraph', 'foreward', 'loi', 'lot', 'notes', 'preface', 'text']

PROTECTED_FILES = [
    'mimetype',
    'META-INF/container.xml',
]

TEXT_MIMETYPES = [
    'image/svg+xml',
    'application/xhtml+xml',
    'text/css',
    'application/x-dtbncx+xml',
    'application/oebps-package+xml',
    'application/oebs-page-map+xml',
    'application/smil+xml',
    'application/adobe-page-template+xml',
    'application/vnd.adobe-page-template+xml',
    'text/javascript',
    'application/javascript'
    'application/pls+xml'
]


def _epub_file_walk(top):
    top = os.fsdecode(top)
    rv = []
    for base, dnames, names in os.walk(top):
        for name in names:
            rv.append(os.path.relpath(os.path.join(base, name), top))
    return rv


class WrapperException(Exception):
    pass

class Wrapper(object):

    def __init__(self, ebook_root, epub_src, outdir, op, plugin_dir, plugin_name, debug=False):
        self._debug = debug
        self.ebook_root = os.fsdecode(ebook_root)
        # plugins and plugin containers can get name and user plugin dir
        self.plugin_dir = os.fsdecode(plugin_dir)
        self.plugin_name = plugin_name
        self.outdir = os.fsdecode(outdir)
        self.epub_filepath = epub_src

        # initialize the sigil cofiguration info passed in outdir with sigil.cfg
        self.opfbookpath = None
        self.appdir = None
        self.usrsupdir = None
        # Location of directory containing hunspell dictionaries on Linux
        self.linux_hunspell_dict_dirs = []
        # Sigil interface language code
        self.sigil_ui_lang = None
        # Default Sigil spell check dictionary
        self.sigil_spellcheck_lang = None
        # status of epub inside Sigil (isDirty) and CurrentFilePath of current epub file
        self.epub_isDirty = False
        self.colormode = None
        self.colors = None
        self.using_automate = False
        self.automate_parameter = None
        # File selected in Sigil's Book Browser
        self.selected = []
        
        self.opfbookpath = op.opf_bookpath
        self.appdir = ""
        self.usrsupdir = ""
        if not sys.platform.startswith('darwin') and not sys.platform.startswith('win'):
            self.linux_hunspell_dict_dirs = ""
        self.sigil_ui_lang = ""
        self.sigil_spellcheck_lang = ""
        self.epub_isDirty = False
        self.colormode = ""
        self.colors = ""
        self.highdpi = ""
        self.uifont = ""
        self.using_automate = ""
        self.automate_parameter = ""
        self.selected = ""

        os.environ['SigilGumboLibPath'] = self.get_gumbo_path()

        # dictionaries used to map opf manifest information
        self.id_to_href = OrderedDict()
        self.id_to_mime = OrderedDict()
        self.id_to_props = OrderedDict()
        self.id_to_fall = OrderedDict()
        self.id_to_over = OrderedDict()
        self.id_to_bookpath = OrderedDict()
        self.href_to_id = OrderedDict()
        self.bookpath_to_id = OrderedDict()
        self.spine_ppd = None
        self.spine = []
        self.guide = []
        self.bindings = []
        self.package_tag = None
        self.epub_version = None
        # self.metadata_attr = None
        # self.metadata = []
        self.metadataxml = ''
        self.op = op
        if self.op is not None:
            # copy in data from parsing of initial opf
            self.opf_dir = op.opf_dir
            # Note: manifest hrefs may only point to files (there are no fragments)
            # all manifest relative hrefs have already had their path component url decoded
            self.id_to_href = op.get_manifest_id_to_href_dict().copy()
            self.id_to_mime = op.get_manifest_id_to_mime_dict().copy()
            self.id_to_props = op.get_manifest_id_to_properties_dict().copy()
            self.id_to_fall = op.get_manifest_id_to_fallback_dict().copy()
            self.id_to_over = op.get_manifest_id_to_overlay_dict().copy()
            self.id_to_bookpath = op.get_manifest_id_to_bookpath_dict().copy()
            self.group_paths = op.get_group_paths().copy()
            self.spine_ppd = op.get_spine_ppd()
            self.spine = op.get_spine()
            # since guide hrefs may contain framents they are kept in url encoded form
            self.guide = op.get_guide()
            self.package_tag = op.get_package_tag()
            self.epub_version = op.get_epub_version()
            self.bindings = op.get_bindings()
            self.metadataxml = op.get_metadataxml()
            # invert key dictionaries to allow for reverse access
            for k, v in self.id_to_href.items():
                self.href_to_id[v] = k
            for k, v in self.id_to_bookpath.items():
                self.bookpath_to_id[v] = k
            # self.href_to_id = {v: k for k, v in self.id_to_href.items()}
            # self.bookpath_to_id = {v: k for k, v in self.id_to_bookpath.items()}
            # self.metadata = op.get_metadata()
            # self.metadata_attr = op.get_metadata_attr()
        self.other = []  # non-manifest file information
        self.id_to_filepath = OrderedDict()
        self.book_href_to_filepath = OrderedDict()
        self.modified = OrderedDict()
        self.added = []
        self.deleted = []

        # walk the ebook directory tree building up initial list of
        # all unmanifested (other) files
        for filepath in _epub_file_walk(ebook_root):
            book_href = filepath.replace(os.sep, "/")
            # OS X file names and paths use NFD form. The EPUB
            # spec requires all text including filenames to be in NFC form.
            book_href = unicodedata.normalize('NFC', book_href)
            # if book_href file in manifest convert to manifest id
            id = self.bookpath_to_id.get(book_href, None)
            if id is None:
                self.other.append(book_href)
                self.book_href_to_filepath[book_href] = filepath
            else:
                self.id_to_filepath[id] = filepath

    def getversion(self):
        global _launcher_version
        return _launcher_version

    def getepubversion(self):
        return self.epub_version

    # utility routine to get mime from href (book href or opf href)
    # no fragments present
    def getmime(self, href):
        href = _unicodestr(href)
        href = urldecodepart(href)
        filename = os.path.basename(href)
        ext = os.path.splitext(filename)[1]
        ext = ext.lower()
        return ext_mime_map.get(ext, "")


    # New in Sigil 1.1
    # ------------------

    # returns color mode of Sigil "light" or "dark"
    def colorMode(self):
        return _unicodestr(self.colormode)

    # returns color as css or javascript hex color string #xxxxxx
    # Accepts the following color roles "Window", "Base", "Text", "Highlight", "HighlightedText"
    def color(self, role):
        role = _unicodestr(role)
        role = role.lower()
        color_roles = ["window", "base", "text", "highlight", "highlightedtext"]
        colors = self.colors.split(',')
        if role in color_roles:
            idx = color_roles.index(role)
            return _unicodestr(colors[idx])
        return None

    # New in Sigil 1.0
    # ----------------

    # A book path (aka "bookpath" or "book_path") is a unique relative path
    # from the ebook root to a specific file.  As a relative path meant to
    # be used in an href or src link it only uses forward slashes "/"
    # as path segment separators.  Since all files exist inside the
    # epub root (folder the epub was unzipped into), book paths will NEVER
    # have or use "./" or "../" ie they are in always in canonical form

    # We will use the terms book_href (aka "bookhref") interchangeabily
    # with bookpath with the following convention:
    #   - use book_href when working with "other" files outside of the manifest
    #   - use bookpath when working with files in the manifest
    #   - use either when the file in question in the OPF as it exists in the intersection

    # returns the bookpath/book_href to the opf file
    def get_opfbookpath(self):
        return self.opfbookpath

    # returns the book path to the folder containing this bookpath
    def get_startingdir(self, bookpath):
        bookpath = _unicodestr(bookpath)
        return startingDir(bookpath)

    # return a bookpath for the file pointed to by the href from
    # the specified bookpath starting directory
    # no fragments allowed in href (must have been previously split off)
    def build_bookpath(self, href, starting_dir):
        href = _unicodestr(href)
        href = urldecodepart(href)
        starting_dir = _unicodestr(starting_dir)
        return buildBookPath(href, starting_dir)

    # returns the href relative path from source bookpath to target bookpath
    def get_relativepath(self, from_bookpath, to_bookpath):
        from_bookpath = _unicodestr(from_bookpath)
        to_bookpath = _unicodestr(to_bookpath)
        return buildRelativePath(from_bookpath, to_bookpath)

    # ----------

    # routine to detect if the current epub is in Sigil standard epub form
    def epub_is_standard(self):
        groups = ["Text", "Styles", "Fonts", "Images", "Audio", "Video", "Misc"]
        paths = ["OEBPS/Text", "OEBPS/Styles", "OEBPS/Fonts", "OEBPS/Images", "OEBPS/Audio", "OEBPS/Video", "OEBPS/Misc"]
        std_epub = self.opfbookpath == "OEBPS/content.opf"
        tocid = self.gettocid()
        if tocid is not None:
            std_epub = std_epub and self.id_to_bookpath[tocid] == "OEBPS/toc.ncx"
        if self.epub_version.startswith("2"):
            std_epub = std_epub and tocid is not None
        for g, p in zip(groups, paths):
            folders = self.group_paths[g]
            std_epub = std_epub and folders[0] == p and len(folders) == 1
        return std_epub


    # routines to rebuild the opf on the fly from current information
    def build_package_starttag(self):
        return self.package_tag

    def build_manifest_xml(self):
        manout = []
        manout.append('  <manifest>\n')
        for id in sorted(self.id_to_mime):
            href = self.id_to_href[id]
            # relative manifest hrefs must have no fragments
            if href.find(':') == -1:
                href = urlencodepart(href)
            mime = self.id_to_mime[id]
            props = ''
            properties = self.id_to_props[id]
            if properties is not None:
                props = ' properties="%s"' % properties
            fall = ''
            fallback = self.id_to_fall[id]
            if fallback is not None:
                fall = ' fallback="%s"' % fallback
            over = ''
            overlay = self.id_to_over[id]
            if overlay is not None:
                over = ' media-overlay="%s"' % overlay
            manout.append('    <item id="%s" href="%s" media-type="%s"%s%s%s />\n' % (id, href, mime, props, fall, over))
        manout.append('  </manifest>\n')
        return "".join(manout)

    def build_spine_xml(self):
        spineout = []
        ppd = ''
        ncx = ''
        map = ''
        if self.spine_ppd is not None:
            ppd = ' page-progression-direction="%s"' % self.spine_ppd
        tocid = self.gettocid()
        if tocid is not None:
            ncx = ' toc="%s"' % tocid
        pagemapid = self.getpagemapid()
        if pagemapid is not None:
            map = ' page-map="%s"' % pagemapid
        spineout.append('  <spine%s%s%s>\n' % (ppd, ncx, map))
        for (id, linear, properties) in self.spine:
            lin = ''
            if linear is not None:
                lin = ' linear="%s"' % linear
            props = ''
            if properties is not None:
                props = ' properties="%s"' % properties
            spineout.append('    <itemref idref="%s"%s%s/>\n' % (id, lin, props))
        spineout.append('  </spine>\n')
        return "".join(spineout)

    def build_guide_xml(self):
        guideout = []
        if len(self.guide) > 0:
            guideout.append('  <guide>\n')
            for (type, title, href) in self.guide:
                # note guide hrefs may have fragments so must be kept
                # in url encoded form at all times until splitting into component parts
                guideout.append('    <reference type="%s" href="%s" title="%s"/>\n' % (type, href, title))
            guideout.append('  </guide>\n')
        return "".join(guideout)

    def build_bindings_xml(self):
        bindout = []
        if len(self.bindings) > 0 and self.epub_version.startswith('3'):
            bindout.append('  <bindings>\n')
            for (mtype, handler) in self.bindings:
                bindout.append('    <mediaType media-type="%s" handler="%s"/>\n' % (mtype, handler))
            bindout.append('  </bindings>\n')
        return "".join(bindout)

    def build_opf(self):
        data = []
        data.append('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        data.append(self.build_package_starttag())
        data.append(self.metadataxml)
        data.append(self.build_manifest_xml())
        data.append(self.build_spine_xml())
        data.append(self.build_guide_xml())
        data.append(self.build_bindings_xml())
        data.append('</package>\n')
        return "".join(data)

    def write_opf(self):
        if self.op is not None:
            platpath = self.opfbookpath.replace('/', os.sep)
            filepath = os.path.join(self.outdir, platpath)
            base = os.path.dirname(filepath)
            if not os.path.exists(base):
                os.makedirs(base)
            with open(filepath, 'wb') as fp:
                data = _utf8str(self.build_opf())
                fp.write(data)


    # routines to help find the manifest id of toc.ncx and page-map.xml

    def gettocid(self):
        for id in self.id_to_mime:
            mime = self.id_to_mime[id]
            if mime == "application/x-dtbncx+xml":
                return id
        return None

    def getpagemapid(self):
        for id in self.id_to_mime:
            mime = self.id_to_mime[id]
            if mime == "application/oebs-page-map+xml":
                return id
        return None


    # routines to help find the manifest id of the nav
    def getnavid(self):
        if self.epub_version == "2.0":
            return None
        for id in self.id_to_mime:
            mime = self.id_to_mime[id]
            if mime == "application/xhtml+xml":
                properties = self.id_to_props[id]
                if properties is not None and "nav" in properties:
                    return id
        return None


    # routines to manipulate the spine

    def getspine(self):
        osp = []
        for (sid, linear, properties) in self.spine:
            osp.append((sid, linear))
        return osp

    def setspine(self, new_spine):
        spine = []
        for (sid, linear) in new_spine:
            properties = None
            sid = _unicodestr(sid)
            linear = _unicodestr(linear)
            if sid not in self.id_to_href:
                raise WrapperException('Spine Id not in Manifest')
            if linear is not None:
                linear = linear.lower()
                if linear not in ['yes', 'no']:
                    raise Exception('Improper Spine Linear Attribute')
            spine.append((sid, linear, properties))
        self.spine = spine
        self.modified[self.opfbookpath] = 'file'

    def getspine_epub3(self):
        return self.spine

    def setspine_epub3(self, new_spine):
        spine = []
        for (sid, linear, properties) in new_spine:
            sid = _unicodestr(sid)
            linear = _unicodestr(linear)
            properties = _unicodestr(properties)
            if properties is not None and properties == "":
                properties = None
            if sid not in self.id_to_href:
                raise WrapperException('Spine Id not in Manifest')
            if linear is not None:
                linear = linear.lower()
                if linear not in ['yes', 'no']:
                    raise Exception('Improper Spine Linear Attribute')
            if properties is not None:
                properties = properties.lower()
            spine.append((sid, linear, properties))
        self.spine = spine
        self.modified[self.opfbookpath] = 'file'

    def getbindings_epub3(self):
        return self.bindings

    def setbindings_epub3(self, new_bindings):
        bindings = []
        for (mtype, handler) in new_bindings:
            mtype = _unicodestr(mtype)
            handler = _unicodestr(handler)
            if mtype is None or mtype == "":
                continue
            if handler is None or handler == "":
                continue
            if handler not in self.id_to_href:
                raise WrapperException('Handler not in Manifest')
            bindings.append((mtype, handler))
        self.bindings = bindings
        self.modified[self.opfbookpath] = 'file'

    def spine_insert_before(self, pos, sid, linear, properties=None):
        sid = _unicodestr(sid)
        linear = _unicodestr(linear)
        properties = _unicodestr(properties)
        if properties is not None and properties == "":
            properties = None
        if sid not in self.id_to_mime:
            raise WrapperException('that spine idref does not exist in manifest')
        n = len(self.spine)
        if pos == 0:
            self.spine = [(sid, linear, properties)] + self.spine
        elif pos == -1 or pos >= n:
            self.spine.append((sid, linear, properties))
        else:
            self.spine = self.spine[0:pos] + [(sid, linear, properties)] + self.spine[pos:]
        self.modified[self.opfbookpath] = 'file'

    def getspine_ppd(self):
        return self.spine_ppd

    def setspine_ppd(self, ppd):
        ppd = _unicodestr(ppd)
        if ppd not in ['rtl', 'ltr', None]:
            raise WrapperException('incorrect page-progression direction')
        self.spine_ppd = ppd
        self.modified[self.opfbookpath] = 'file'

    def setspine_itemref_epub3_attributes(self, idref, linear, properties):
        idref = _unicodestr(idref)
        linear = _unicodestr(linear)
        properties = _unicodestr(properties)
        if properties is not None and properties == "":
            properties = None
        pos = -1
        i = 0
        for (sid, slinear, sproperties) in self.spine:
            if sid == idref:
                pos = i
                break
            i += 1
        if pos == -1:
            raise WrapperException('that idref is not exist in the spine')
        self.spine[pos] = (sid, linear, properties)
        self.modified[self.opfbookpath] = 'file'


    # routines to get and set the guide

    def getguide(self):
        return self.guide

    # guide hrefs must be in urlencoded form (percent encodings present if needed)
    # as they may include fragments and # is a valid url path character
    def setguide(self, new_guide):
        guide = []
        for (type, title, href) in new_guide:
            type = _unicodestr(type)
            title = _unicodestr(title)
            href = _unicodestr(href)
            if type not in _guide_types:
                type = "other." + type
            if title is None:
                title = 'title missing'
            thref = urldecodepart(href.split('#')[0])
            if thref not in self.href_to_id:
                raise WrapperException('guide href not in manifest')
            guide.append((type, title, href))
        self.guide = guide
        self.modified[self.opfbookpath] = 'file'


    # routines to get and set metadata xml fragment

    def getmetadataxml(self):
        return self.metadataxml

    def setmetadataxml(self, new_metadata):
        self.metadataxml = _unicodestr(new_metadata)
        self.modified[self.opfbookpath] = 'file'


    # routines to get and set the package tag
    def getpackagetag(self):
        return self.package_tag

    def setpackagetag(self, new_packagetag):
        pkgtag = _unicodestr(new_packagetag)
        version = ""
        mo = _PKG_VER.search(pkgtag)
        if mo:
            version = mo.group(1)
        if version != self.epub_version:
            raise WrapperException('Illegal to change the package version attribute')
        self.package_tag = pkgtag
        self.modified[self.opfbookpath] = 'file'


    # routines to manipulate files in the manifest (updates the opf automagically)

    def readfile(self, id):
        id = _unicodestr(id)
        if id not in self.id_to_href:
            raise WrapperException('Id does not exist in manifest')
        filepath = self.id_to_filepath.get(id, None)
        if filepath is None:
            raise WrapperException('Id does not exist in manifest')
        # already added or modified it will be in outdir
        basedir = self.ebook_root
        if id in self.added or id in self.modified:
            basedir = self.outdir
        filepath = os.path.join(basedir, filepath)
        if not os.path.exists(filepath):
            raise WrapperException('File Does Not Exist')
        data = ''
        with open(filepath, 'rb') as fp:
            data = fp.read()
        mime = self.id_to_mime.get(id, '')
        if mime in TEXT_MIMETYPES:
            data = _unicodestr(data)
        return data

    def writefile(self, id, data):
        id = _unicodestr(id)
        if id not in self.id_to_href:
            raise WrapperException('Id does not exist in manifest')
        filepath = self.id_to_filepath.get(id, None)
        if filepath is None:
            raise WrapperException('Id does not exist in manifest')
        mime = self.id_to_mime.get(id, '')
        filepath = os.path.join(self.outdir, filepath)
        base = os.path.dirname(filepath)
        if not os.path.exists(base):
            os.makedirs(base)
        if mime in TEXT_MIMETYPES or isinstance(data, str):
            data = _utf8str(data)
        with open(filepath, 'wb') as fp:
            fp.write(data)
        self.modified[id] = 'file'


    def addfile(self, uniqueid, basename, data, mime=None, properties=None, fallback=None, overlay=None):
        uniqueid = _unicodestr(uniqueid)
        if uniqueid in self.id_to_href:
            raise WrapperException('Manifest Id is not unique')
        basename = _unicodestr(basename)
        mime = _unicodestr(mime)
        if mime is None:
            ext = os.path.splitext(basename)[1]
            ext = ext.lower()
            mime = ext_mime_map.get(ext, None)
        if mime is None:
            raise WrapperException("Mime Type Missing")
        if mime == "application/x-dtbncx+xml" and self.epub_version.startswith("2"):
            raise WrapperException('Can not add or remove an ncx under epub2')
        group = mime_group_map.get(mime, "Misc")
        default_path = self.group_paths[group][0]
        bookpath = basename
        if default_path != "":
            bookpath = default_path + "/" + basename
        href = buildRelativePath(self.opfbookpath, bookpath)
        if href in self.href_to_id:
            raise WrapperException('Basename already exists')
        # now actually write out the new file
        filepath = bookpath.replace("/", os.sep)
        self.id_to_filepath[uniqueid] = filepath
        filepath = os.path.join(self.outdir, filepath)
        base = os.path.dirname(filepath)
        if not os.path.exists(base):
            os.makedirs(base)
        if mime in TEXT_MIMETYPES or isinstance(data, str):
            data = _utf8str(data)
        with open(filepath, 'wb') as fp:
            fp.write(data)
        self.id_to_href[uniqueid] = href
        self.id_to_mime[uniqueid] = mime
        self.id_to_props[uniqueid] = properties
        self.id_to_fall[uniqueid] = fallback
        self.id_to_over[uniqueid] = overlay
        self.id_to_bookpath[uniqueid] = bookpath
        self.href_to_id[href] = uniqueid
        self.bookpath_to_id[bookpath] = uniqueid
        self.added.append(uniqueid)
        self.modified[self.opfbookpath] = 'file'
        return uniqueid


    # new in Sigil 1.0

    # adds bookpath specified file to the manifest with given uniqueid data, and mime
    def addbookpath(self, uniqueid, bookpath, data, mime=None):
        uniqueid = _unicodestr(uniqueid)
        if uniqueid in self.id_to_href:
            raise WrapperException('Manifest Id is not unique')
        bookpath = _unicodestr(bookpath)
        basename = bookpath.split("/")[-1]
        mime = _unicodestr(mime)
        if mime is None:
            ext = os.path.splitext(basename)[1]
            ext = ext.lower()
            mime = ext_mime_map.get(ext, None)
        if mime is None:
            raise WrapperException("Mime Type Missing")
        if mime == "application/x-dtbncx+xml" and self.epub_version.startswith("2"):
            raise WrapperException('Can not add or remove an ncx under epub2')
        href = buildRelativePath(self.opfbookpath, bookpath)
        if href in self.href_to_id:
            raise WrapperException('bookpath already exists')
        # now actually write out the new file
        filepath = bookpath.replace("/", os.sep)
        self.id_to_filepath[uniqueid] = filepath
        filepath = os.path.join(self.outdir, filepath)
        base = os.path.dirname(filepath)
        if not os.path.exists(base):
            os.makedirs(base)
        if mime in TEXT_MIMETYPES or isinstance(data, str):
            data = _utf8str(data)
        with open(filepath, 'wb') as fp:
            fp.write(data)
        self.id_to_href[uniqueid] = href
        self.id_to_mime[uniqueid] = mime
        self.id_to_props[uniqueid] = None
        self.id_to_fall[uniqueid] = None
        self.id_to_over[uniqueid] = None
        self.id_to_bookpath[uniqueid] = bookpath
        self.href_to_id[href] = uniqueid
        self.bookpath_to_id[bookpath] = uniqueid
        self.added.append(uniqueid)
        self.modified[self.opfbookpath] = 'file'
        return uniqueid


    def deletefile(self, id):
        id = _unicodestr(id)
        if id not in self.id_to_href:
            raise WrapperException('Id does not exist in manifest')
        filepath = self.id_to_filepath.get(id, None)
        if id is None:
            raise WrapperException('Id does not exist in manifest')
        if self.epub_version.startswith("2") and id == self.gettocid():
            raise WrapperException('Can not add or remove an ncx under epub2')
        add_to_deleted = True
        # if file was added or modified, delete file from outdir
        if id in self.added or id in self.modified:
            filepath = os.path.join(self.outdir, filepath)
            if os.path.exists(filepath) and os.path.isfile(filepath):
                os.remove(filepath)
            if id in self.added:
                self.added.remove(id)
                add_to_deleted = False
            if id in self.modified:
                del self.modified[id]
        # remove from manifest
        href = self.id_to_href[id]
        bookpath = self.id_to_bookpath[id]
        del self.id_to_href[id]
        del self.id_to_mime[id]
        del self.id_to_props[id]
        del self.id_to_fall[id]
        del self.id_to_over[id]
        del self.id_to_bookpath[id]
        del self.href_to_id[href]
        del self.bookpath_to_id[bookpath]
        # remove from spine
        new_spine = []
        was_modified = False
        for sid, linear, properties in self.spine:
            if sid != id:
                new_spine.append((sid, linear, properties))
            else:
                was_modified = True
        if was_modified:
            self.setspine_epub3(new_spine)
        if add_to_deleted:
            self.deleted.append(('manifest', id, bookpath))
            self.modified[self.opfbookpath] = 'file'
        del self.id_to_filepath[id]

    def set_manifest_epub3_attributes(self, id, properties=None, fallback=None, overlay=None):
        id = _unicodestr(id)
        properties = _unicodestr(properties)
        if properties is not None and properties == "":
            properties = None
        fallback = _unicodestr(fallback)
        if fallback is not None and fallback == "":
            fallback = None
        overlay = _unicodestr(overlay)
        if overlay is not None and overlay == "":
            overlay = None
        if id not in self.id_to_href:
            raise WrapperException('Id does not exist in manifest')
        del self.id_to_props[id]
        del self.id_to_fall[id]
        del self.id_to_over[id]
        self.id_to_props[id] = properties
        self.id_to_fall[id] = fallback
        self.id_to_over[id] = overlay
        self.modified[self.opfbookpath] = 'file'


    # helpful mapping routines for file info from the opf manifest

    def map_href_to_id(self, href, ow):
        href = _unicodestr(href)
        href = urldecodepart(href)
        return self.href_to_id.get(href, ow)

    # new in Sigil 1.0
    def map_bookpath_to_id(self, bookpath, ow):
        bookpath = _unicodestr(bookpath)
        return self.bookpath_to_id.get(bookpath, ow)

    def map_basename_to_id(self, basename, ow):
        for bookpath in self.bookpath_to_id:
            filename = bookpath.split("/")[-1]
            if filename == basename:
                return self.bookpath_to_id[bookpath]
        return ow

    def map_id_to_href(self, id, ow):
        id = _unicodestr(id)
        return self.id_to_href.get(id, ow)

    # new in Sigil 1.0
    def map_id_to_bookpath(self, id, ow):
        id = _unicodestr(id)
        return self.id_to_bookpath.get(id, ow)

    def map_id_to_mime(self, id, ow):
        id = _unicodestr(id)
        return self.id_to_mime.get(id, ow)

    def map_id_to_properties(self, id, ow):
        id = _unicodestr(id)
        return self.id_to_props.get(id, ow)

    def map_id_to_fallback(self, id, ow):
        id = _unicodestr(id)
        return self.id_to_fall.get(id, ow)

    def map_id_to_overlay(self, id, ow):
        id = _unicodestr(id)
        return self.id_to_over.get(id, ow)

    # new in Sigil 1.0
    # returns a sorted folder list for that group
    # valid groups: Text, Styles, Images, Fonts, Audio, Video, ncx, opf, Misc
    def map_group_to_folders(self, group, ow):
        group = _unicodestr(group)
        return self.group_paths.get(group, ow)

    # new in Sigil 1.0
    def map_mediatype_to_group(self, mtype, ow):
        mtype = _unicodestr(mtype)
        return mime_group_map.get(mtype, ow)


    # routines to work on ebook files that are not part of an opf manifest
    # their "id" is actually their unique relative path from book root
    # this is called either a book href or a book path
    # we use book_href or bookhref  when working with "other" files
    # we use bookpath when working with files in the manifest

    def readotherfile(self, book_href):
        id = _unicodestr(book_href)
        id = urldecodepart(id)
        if id is None:
            raise WrapperException('None is not a valid book href')
        if id not in self.other and id in self.id_to_href:
            raise WrapperException('Incorrect interface routine - use readfile')
        # handle special case of trying to read the opf after it has been modified
        if id == self.opfbookpath:
            if id in self.modified:
                return self.build_opf()
        filepath = self.book_href_to_filepath.get(id, None)
        if filepath is None:
            raise WrapperException('Book href does not exist')
        basedir = self.ebook_root
        if id in self.added or id in self.modified:
            basedir = self.outdir
        filepath = os.path.join(basedir, filepath)
        if not os.path.exists(filepath):
            raise WrapperException('File Does Not Exist')
        basename = os.path.basename(filepath)
        ext = os.path.splitext(basename)[1]
        ext = ext.lower()
        mime = ext_mime_map.get(ext, "")
        data = b''
        with open(filepath, 'rb') as fp:
            data = fp.read()
        if mime in TEXT_MIMETYPES:
            data = _unicodestr(data)
        return data

    def writeotherfile(self, book_href, data):
        id = _unicodestr(book_href)
        id = urldecodepart(id)
        if id is None:
            raise WrapperException('None is not a valid book href')
        if id not in self.other and id in self.id_to_href:
            raise WrapperException('Incorrect interface routine - use writefile')
        filepath = self.book_href_to_filepath.get(id, None)
        if filepath is None:
            raise WrapperException('Book href does not exist')
        if id in PROTECTED_FILES or id == self.opfbookpath:
            raise WrapperException('Attempt to modify protected file')
        filepath = os.path.join(self.outdir, filepath)
        base = os.path.dirname(filepath)
        if not os.path.exists(base):
            os.makedirs(base)
        if isinstance(data, str):
            data = _utf8str(data)
        with open(filepath, 'wb') as fp:
            fp.write(data)
        self.modified[id] = 'file'

    def addotherfile(self, book_href, data) :
        id = _unicodestr(book_href)
        id = urldecodepart(id)
        if id is None:
            raise WrapperException('None is not a valid book href')
        if id in self.other:
            raise WrapperException('Book href must be unique')
        desired_path = id.replace("/", os.sep)
        filepath = os.path.join(self.outdir, desired_path)
        if os.path.isfile(filepath):
            raise WrapperException('Desired path already exists')
        base = os.path.dirname(filepath)
        if not os.path.exists(base):
            os.makedirs(base)
        if isinstance(data, str):
            data = _utf8str(data)
        with open(filepath, 'wb')as fp:
            fp.write(data)
        self.other.append(id)
        self.added.append(id)
        self.book_href_to_filepath[id] = desired_path

    def deleteotherfile(self, book_href):
        id = _unicodestr(book_href)
        id = urldecodepart(id)
        if id is None:
            raise WrapperException('None is not a valid book hrefbook href')
        if id not in self.other and id in self.id_to_href:
            raise WrapperException('Incorrect interface routine - use deletefile')
        filepath = self.book_href_to_filepath.get(id, None)
        if filepath is None:
            raise WrapperException('Book href does not exist')
        if id in PROTECTED_FILES or id == self.opfbookpath:
            raise WrapperException('attempt to delete protected file')
        add_to_deleted = True
        # if file was added or modified delete file from outdir
        if id in self.added or id in self.modified:
            filepath = os.path.join(self.outdir, filepath)
            if os.path.exists(filepath) and os.path.isfile(filepath):
                os.remove(filepath)
            if id in self.added:
                self.added.remove(id)
                add_to_deleted = False
            if id in self.other:
                self.other.remove(id)
            if id in self.modified:
                del self.modified[id]
        if add_to_deleted:
            self.deleted.append(('other', id, book_href))
        del self.book_href_to_filepath[id]


    # utility routine to copy entire ebook to a destination directory
    # including the any prior updates and changes to the opf

    def copy_book_contents_to(self, destdir):
        destdir = _unicodestr(destdir)
        if destdir is None or not os.path.isdir(destdir):
            raise WrapperException('destination directory does not exist')
        for id in self.id_to_filepath:
            rpath = self.id_to_filepath[id]
            data = self.readfile(id)
            filepath = os.path.join(destdir, rpath)
            base = os.path.dirname(filepath)
            if not os.path.exists(base):
                os.makedirs(base)
            if isinstance(data, str):
                data = _utf8str(data)
            with open(filepath, 'wb') as fp:
                fp.write(data)
        for id in self.book_href_to_filepath:
            rpath = self.book_href_to_filepath[id]
            data = self.readotherfile(id)
            filepath = os.path.join(destdir, rpath)
            base = os.path.dirname(filepath)
            if not os.path.exists(base):
                os.makedirs(base)
            if isinstance(data, str):
                data = _utf8str(data)
            with open(filepath, 'wb') as fp:
                fp.write(data)

    def get_dictionary_dirs(self):
        apaths = []
        if sys.platform.startswith('darwin'):
            apaths.append(os.path.abspath(os.path.join(self.appdir, "..", "hunspell_dictionaries")))
            apaths.append(os.path.abspath(os.path.join(self.usrsupdir, "hunspell_dictionaries")))
        elif sys.platform.startswith('win'):
            apaths.append(os.path.abspath(os.path.join(self.appdir, "hunspell_dictionaries")))
            apaths.append(os.path.abspath(os.path.join(self.usrsupdir, "hunspell_dictionaries")))
        else:
            # Linux
            for path in self.linux_hunspell_dict_dirs:
                apaths.append(os.path.abspath(path.strip()))
            apaths.append(os.path.abspath(os.path.join(self.usrsupdir, "hunspell_dictionaries")))
        return apaths

    def get_gumbo_path(self):
        if sys.platform.startswith('darwin'):
            lib_dir = os.path.abspath(os.path.join(self.appdir, "..", "lib"))
            lib_name = 'libsigilgumbo.dylib'
        elif sys.platform.startswith('win'):
            lib_dir = os.path.abspath(self.appdir)
            lib_name = 'sigilgumbo.dll'
        else:
            lib_dir = os.path.abspath(self.appdir)
            lib_name = 'libsigilgumbo.so'
        return os.path.join(lib_dir, lib_name)

    def get_hunspell_path(self):
        if sys.platform.startswith('darwin'):
            lib_dir = os.path.abspath(os.path.join(self.appdir, "..", "lib"))
            lib_name = 'libhunspell.dylib'
        elif sys.platform.startswith('win'):
            lib_dir = os.path.abspath(self.appdir)
            lib_name = 'hunspell.dll'
        else:
            lib_dir = os.path.abspath(self.appdir)
            lib_name = 'libhunspell.so'
        return os.path.join(lib_dir, lib_name)


    #====================================================================================
    # 以下均为添加的方法，非Sigil插件原生方法
    #====================================================================================

    def save_as(self,save_path=""):

        self.write_opf()

        def copy_file(src_path,dst_path):
            dst_dir = os.path.dirname(dst_path)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            with open(src_path,"rb") as src_fp:
                with open(dst_path,"wb") as dst_fp:
                    dst_fp.write(src_fp.read())

        for ftype, id, bookhref in self.deleted:
            filepath = os.path.join(self.ebook_root,bookhref)
            if os.path.exists(filepath):
                os.remove(filepath)

        # clear empty folders
        empty_dirs = []
        while True:
            for basedir,dnames,fnames in os.walk(self.ebook_root):
                if dnames == [] and fnames == []:
                    empty_dirs.append(basedir)
            if empty_dirs == []:
                break
            for empty_dir in empty_dirs:
                os.removedirs(empty_dir)
            empty_dirs.clear()

        for id in self.added:
            if self.id_to_bookpath.get(id):
                bookhref = self.id_to_bookpath[id]
            else:
                bookhref = id
            src_path = os.path.join(self.outdir,bookhref)
            dst_path = os.path.join(self.ebook_root,bookhref)
            copy_file(src_path,dst_path)

        for id in self.modified:
            if self.id_to_bookpath.get(id):
                bookhref = self.id_to_bookpath[id]
            else:
                bookhref = id
            src_path = os.path.join(self.outdir,bookhref)
            dst_path = os.path.join(self.ebook_root,bookhref)
            copy_file(src_path,dst_path)

        if save_path == '':
            epub_name = os.path.basename(self.epub_filepath)
            save_path = os.path.join(os.path.dirname(self.epub_filepath),'OUTPUT',epub_name)
        dirname = os.path.dirname(save_path)
        if dirname != '' and not os.path.exists(dirname):
            os.makedirs(dirname)

        with zipfile.ZipFile(save_path,'w',zipfile.ZIP_DEFLATED) as outfile:
            for bookpath in _epub_file_walk(self.ebook_root):
                realpath = os.path.join(self.ebook_root,bookpath)
                with open(realpath,'rb') as f:
                    data = f.read()
                outfile.writestr(bookpath, data, zipfile.ZIP_DEFLATED)

        self.deleted.clear()
        self.added.clear()
        self.modified.clear()

    def __del__(self):
        if self.ebook_root:
            workspace = os.path.dirname(self.ebook_root)
            shutil.rmtree(workspace)
            print("Wrapper: 程序运行结束，已删除临时目录。")


    def standardize_epub(self):
        if self.epub_is_standard():
            return
        opfpath = "OEBPS/content.opf"
        # group_paths 会影响到 addfile 添加文件的目录
        self.group_paths = std_group_paths = {
            "Text"   : ["OEBPS/Text"],
            "Styles" : ["OEBPS/Styles"],
            "Fonts"  : ["OEBPS/Fonts"],
            "Images" : ["OEBPS/Images"],
            "Audio"  : ["OEBPS/Audio"],
            "Video"  : ["OEBPS/Video"],
            "Misc"   : ["OEBPS/Misc"],
            "ncx"    : ["OEBPS"],
            "opf"    : ["OEBPS"]
        }
        std_opfpath = "OEBPS/content.opf"
        std_tocpath = "OEBPS/toc.ncx"
        deleted = [] # [(id,bkpath,mime,prop,fall,over)]
        basename_list = [] # [basename]
        toc_id = self.gettocid()
        oldBkpath_to_newBasename = {} # [ old_bkpath.lower() : new_basename ]
        newBkpath_to_oldGroup = {} # [ new_bkpath : old_group ]
        old_opfpath = self.opfbookpath

        def no_repeat_basename(basename):
            nonlocal basename_list
            while basename in basename_list:
                nameWithoutExt, ext = os.path.splitext(basename)
                nameWithoutExt += "_"
                basename = nameWithoutExt + ext
            basename_list.append(basename)
            return basename

        # 清理关联文件不存在的ID。
        ids_not_in_manifest = []
        for id in self.id_to_bookpath.keys():
            if self.id_to_filepath.get(id) is None:
                ids_not_in_manifest.append(id)
        for id in ids_not_in_manifest:
            href = self.id_to_href[id]
            bookpath = self.id_to_bookpath[id]
            del self.id_to_href[id]
            del self.id_to_mime[id]
            del self.id_to_props[id]
            del self.id_to_fall[id]
            del self.id_to_over[id]
            del self.id_to_bookpath[id]
            del self.href_to_id[href]
            del self.bookpath_to_id[bookpath]

        # 检测并修改 opf 文件归档路径
        if self.opfbookpath != std_opfpath:
            if std_opfpath in self.other:
                self.deleteotherfile(std_opfpath)
            opf_data = self.readotherfile(self.opfbookpath)
            self.addotherfile(std_opfpath,opf_data)
            self.opfbookpath = std_opfpath # 先修改 self.opfbookpath，删除旧opf才不会受限。
            self.opf_dir = "OEBPS"
            self.deleteotherfile(old_opfpath)
            self.other.remove(old_opfpath)
            basename_list.append(os.path.dirname(self.opfbookpath))

        # 检查并修改 toc 文件归档路径
        if toc_id is not None:
            toc_bkpath = self.id_to_bookpath.get(toc_id)
            if self.id_to_bookpath.get(toc_id) != std_tocpath:
                mime = "application/x-dtbncx+xml"
                self.id_to_mime[toc_id] = ""
                data = self.readfile(toc_id)
                self.deletefile(toc_id)
                epub_version = self.epub_version
                self.epub_version = "" # 暂时修改epub_version以绕过epub2对ncx文件的操作限制
                self.addfile(toc_id,"toc.ncx",data,mime)
                self.epub_version = epub_version # 恢复 epub_version
                basename_list.append("toc.ncx")
            oldBkpath_to_newBasename[toc_bkpath.lower()] = "toc.ncx"
            newBkpath_to_oldGroup["OEBPS/toc.ncx"] = os.path.dirname(toc_bkpath)

        # 检查 manifest 文件归档路径
        for id, bkpath in self.id_to_bookpath.items():
            mime = self.id_to_mime[id]
            cur_group_path = os.path.dirname(bkpath)
            std_group = mime_group_map.get(mime)
            std_group_path = std_group_paths.get(std_group)[0]

            if mime == "application/x-dtbncx+xml":
                if id != toc_id:
                    deleted.append((id,bkpath,mime,prop,fall,over))
                continue

            if cur_group_path != std_group_path:
                prop = self.id_to_props.get(id)
                fall = self.id_to_fall.get(id)
                over = self.id_to_over.get(id)
                deleted.append((id,bkpath,mime,prop,fall,over))
            else:
                basename = os.path.basename(bkpath)
                basename_list.append(basename)
                oldBkpath_to_newBasename[bkpath.lower()] = basename
                newBkpath_to_oldGroup[bkpath] = os.path.dirname(bkpath)

        # 检查非 manifest 文件归档路径
        for bkpath in self.other:
            cur_group_path = os.path.dirname(bkpath)
            # META-INF 里除了有 xml，可能还有calibre书签txt文件，某些阅读器的js文件。
            # 所有置于该目录下的文件都不处理。
            if cur_group_path == "META-INF":
                basename = os.path.dirname(bkpath)
                basename_list.append(basename)
                oldBkpath_to_newBasename[bkpath.lower()] = basename
                newBkpath_to_oldGroup[bkpath] = os.path.dirname(bkpath)
                continue

            if bkpath == self.opfbookpath:
                continue

            if bkpath == "mimetype":
                basename = os.path.dirname(bkpath)
                basename_list.append(basename)
                continue

            id = mime = prop = fall = over = None
            deleted.append((id,bkpath,mime,prop,fall,over))

        # 暂时清空 spine 列表是为了避免每次使用deletefile方法遍历一次spine列表，这可能导致文件量大时效率低下。
        spine_bak = self.spine.copy()
        self.spine = []
        # 纠正不标准的归档路径
        for id,bkpath,mime,prop,fall,over in deleted: # files in manifest
            if id is not None: # manifest_id
                if mime == "application/x-dtbncx+xml": # 多余的 ncx 文件，直接删除
                    self.id_to_mime[id] = ""
                    self.deletefile(id)
                    continue
                std_group = mime_group_map.get(mime)
                if std_group is not None:
                    std_group_path = std_group_paths[std_group][0]
                    data = self.readfile(id)
                    self.deletefile(id)
                    basename = no_repeat_basename(os.path.basename(bkpath))
                    oldBkpath_to_newBasename[bkpath.lower()] = basename
                    new_bkpath = std_group_path + "/" + basename
                    newBkpath_to_oldGroup[new_bkpath] = os.path.dirname(bkpath)
                    self.addfile(id,basename,data,mime,prop,fall,over)
                else:
                    self.deletefile(id)
                continue

            else: # files not in manifest
                basename = no_repeat_basename(os.path.basename(bkpath))
                data = self.readotherfile(bkpath)
                self.deleteotherfile(bkpath)
                self.other.remove(bkpath)
                _,ext = os.path.splitext(basename)
                if ext.lower() == "xml":
                    self.addotherfile("META-INF/%s"%(basename),data)
                    continue
                if ext.lower() in ["opf","ncx"]: # 多余的 opf 和 ncx，直接删除
                    continue
                id = basename
                mime = ext_mime_map.get(ext)
                std_group = mime_group_map.get(mime)
                if std_group is not None: # files can register in manifest
                    std_group_path = std_group_paths[std_group][0]
                    oldBkpath_to_newBasename[bkpath.lower()] = basename
                    new_bkpath = std_group_path + "/" + basename
                    newBkpath_to_oldGroup[new_bkpath] = os.path.dirname(bkpath)
                    self.addfile(id,basename,data,mime,None,None,None)
                    if mime == ext_mime_map[".xhtml"]:
                        spine_bak.append((id,None,None))
                else:
                    continue

        # 修改 toc 关联链接
        if toc_id is not None:
            toc = self.readfile(toc_id)
            tocpath = self.id_to_bookpath[toc_id]
            old_toc_dir = newBkpath_to_oldGroup[tocpath]
            def sub_toc_href(match):
                href = match.group(2)
                if href == "" or href.startswith(("http:","https:","res:","file:","data:")):
                    return match.group()
                href = urldecodepart(href).strip()
                if "#" in href:
                    href,target_id = href.split('#')
                    target_id = '#' + target_id
                else:
                    target_id = ''
                bkpath = self.build_bookpath(href, old_toc_dir)
                if oldBkpath_to_newBasename.get(bkpath.lower()):
                    basename = oldBkpath_to_newBasename[bkpath.lower()]
                    return 'src="Text/' + basename + '"' + target_id
                else:
                    return match.group()    
            toc = re.sub(r'src=([\'\"])(.*?)\1',sub_toc_href,toc)
            self.writefile(toc_id,toc)

        # 修改 xhtml 关联链接
        for id,bkpath in self.id_to_bookpath.items():
            if self.id_to_mime.get(id) != "application/xhtml+xml":
                continue
            text = self.readfile(id)
            if not text.startswith('<?xml'):
                text = '<?xml version="1.0" encoding="utf-8"?>\n'+ text
            if not re.match(r'(?s).*<!DOCTYPE html',text):
                if self.epub_version.startswith("2"):
                    text = re.sub(r'(<\?xml.*?>)\n*',r'\1\n<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"\n  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n',text,1)
                elif self.epub_version.startswith("3"):
                    text = re.sub(r'(<\?xml.*?>)\n*',r'\1\n<!DOCTYPE html>\n',text,1)
             #修改a[href]

            def sub_href(match):
                href = match.group(3)
                if href == "" or href.startswith(("http:","https:","res:","file:","data:")):
                    return match.group()
                href = urldecodepart(href).strip()
                if "#" in href:
                    href,target_id = href.split('#')
                    target_id = '#' + target_id
                else:
                    target_id = ''
                old_group = newBkpath_to_oldGroup[bkpath]
                old_bkpath = self.build_bookpath(href,old_group)
                if not old_bkpath:
                    return match.group()

                if href.lower().endswith(('.jpg','.jpeg','.png','.bmp','.gif','.webp','.svg')):
                    filename = oldBkpath_to_newBasename[old_bkpath.lower()]
                    return match.group(1) + '../Images/' + filename + match.group(4)
                elif href.lower().endswith('.css'):
                    filename = oldBkpath_to_newBasename[old_bkpath.lower()]
                    return '<link href="../Styles/' + filename +'" type="text/css" rel="stylesheet"/>'
                elif href.lower().endswith(('.xhtml','.html','.htm')):
                    filename = oldBkpath_to_newBasename[old_bkpath.lower()]
                    return match.group(1) + filename + target_id + match.group(4)
                else:
                    return match.group()    
            text = re.sub(r'(<[^>]*href=([\'\"]))(.*?)(\2[^>]*>)',sub_href,text)

            #修改src
            def re_src(match):
                href = match.group(3)
                if href == "" or href.startswith(("http:","https:","res:","file:","data:")):
                    return match.group()
                href = urldecodepart(href).strip()
                old_group = newBkpath_to_oldGroup[bkpath]
                old_bkpath = self.build_bookpath(href, old_group)
                if not old_bkpath:
                    return match.group()

                if href.lower().endswith(('.jpg','.jpeg','.png','.bmp','.gif','.webp','.svg')):
                    filename = oldBkpath_to_newBasename[old_bkpath.lower()]
                    return match.group(1) + '../Images/' + filename + match.group(4)
                elif href.lower().endswith('.mp3'):
                    filename = oldBkpath_to_newBasename[old_bkpath.lower()]
                    return match.group(1) + '../Audio/' + filename + match.group(4)
                elif href.lower().endswith('.mp4'):
                    filename = oldBkpath_to_newBasename[old_bkpath.lower()]
                    return match.group(1) + '../Video/' + filename + match.group(4)
                elif href.lower().endswith('.js'):
                    filename = oldBkpath_to_newBasename[old_bkpath.lower()]
                    return match.group(1) + '../Misc/' + filename + match.group(4)
                else:
                    return match.group()
            text = re.sub(r'(<[^>]* src=([\'\"]))(.*?)(\2[^>]*>)',re_src,text)

            #修改 url
            def re_url(match):
                url = match.group(2)
                if url == "" or url.startswith(("http:","https:","res:","file:","data:")):
                    return match.group()
                url = urldecodepart(url).strip()
                old_group = newBkpath_to_oldGroup[bkpath]
                old_bkpath = self.build_bookpath(url,old_group)
                if not old_bkpath:
                    return match.group()

                if url.lower().endswith(('.ttf','.otf')):
                    filename = oldBkpath_to_newBasename[old_bkpath.lower()]
                    return match.group(1) + '../Fonts/' + filename + match.group(3)
                elif url.lower().endswith(('.jpg','.jpeg','.png','.bmp','.gif','.webp','.svg')):
                    filename = oldBkpath_to_newBasename[old_bkpath.lower()]
                    return match.group(1) + '../Images/' + filename + match.group(3)
                else:
                    return match.group()
            text = re.sub(r'(url\([\'\"]?)(.*?)([\'\"]?\))',re_url,text)
            self.writefile(id, text)
        
        # 修改css文件关联链接
        for id,bkpath in self.id_to_bookpath.items():
            if self.id_to_mime.get(id) != "text/css":
                continue
            css = self.readfile(id)
            #修改 @import 
            def re_import(match):
                if match.group(2):
                    href = match.group(2)
                else:
                    href = match.group(3)
                href = urldecodepart(href).strip()
                if not href.lower().endswith('.css'):
                    return match.group()
                filename = os.path.basename(href)
                return '@import "' + filename + '"'
            css = re.sub(r'@import ([\'\"])(.*?)\1|@import url\([\'\"]?(.*?)[\'\"]?\)',re_import,css)
            #修改 css的url
            def re_css_url(match):
                url = match.group(2)
                if url == "" or url.startswith(("http:","https:","res:","file:","data:")):
                    return match.group()
                url = urldecodepart(url).strip()
                old_group = newBkpath_to_oldGroup[bkpath]
                old_bkpath = self.build_bookpath(url,old_group)
                if not old_bkpath:
                    return match.group()
                
                if url.lower().endswith(('.ttf','.otf')):
                    filename = oldBkpath_to_newBasename[old_bkpath.lower()]
                    return match.group(1) + '../Fonts/' + filename + match.group(3)
                elif url.lower().endswith(('.jpg','.jpeg','.png','.bmp','.gif','.webp','.svg')):
                    filename = oldBkpath_to_newBasename[old_bkpath.lower()]
                    return match.group(1) + '../Images/' + filename + match.group(3)
                else:
                    return match.group()
            css = re.sub(r'(url\([\'\"]?)(.*?)([\'\"]?\))',re_css_url,css)
            self.writefile(id,css)

        # 修改 opf 的 guide 节点引用链接
        new_guide = []
        for (type, title, href) in self.guide:
            _,ext = os.path.splitext(href)
            group = mime_group_map.get(ext_mime_map.get(ext))
            if group is None:
                new_guide.append((type,title,href))
                continue
            old_opf_dir = os.path.dirname(old_opfpath)
            old_bkpath = self.build_bookpath(href,old_opf_dir)
            new_basename = oldBkpath_to_newBasename.get(old_bkpath.lower())
            if new_basename is None:
                new_guide.append((type,title,href))
                continue

            new_href =  group + "/" + new_basename
            new_guide.append((type,title,new_href))
        
        self.guide = new_guide

        # 恢复 spine 
        self.spine = spine_bak

        # 绕过文件保护，强制改写 container.xml
        container_xml_path = "META-INF/container.xml"
        xml_data = _unicodestr(self.readotherfile(container_xml_path))
        xml_data = re.sub(r'(<rootfile[^>]*full-path="){0}("[^>]*>)'.format(old_opfpath),r"\1"+std_opfpath+r"\2",xml_data)
        xmlpath = self.book_href_to_filepath.get(container_xml_path, None)
        if xmlpath is None:
            raise WrapperException('Book href does not exist')
        xmlpath = os.path.join(self.ebook_root, xmlpath)
        with open(xmlpath, 'wb') as fp:
            fp.write(_utf8str(xml_data))