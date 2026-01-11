#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Copyright (c) 2015-2020 Kevin B. Hendricks, and Doug Massay
# Copyright (c) 2014      Kevin B. Hendricks, John Schember, and Doug Massay
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

from quickparser import QuickXHTMLParser
from preferences import JSONPrefs
from pluginhunspell import HunspellChecker
import typing
class ContainerException(Exception):
    pass

class BookContainer(object):

    def __init__(self, wrapper, debug=False):
        self._debug = debug
        self._w = wrapper
        self.qp = QuickXHTMLParser()
        self.hspell = HunspellChecker(wrapper.get_hunspell_path())
        self.dictionary_dirs = wrapper.get_dictionary_dirs()
        self._prefs_store = JSONPrefs(wrapper.plugin_dir, wrapper.plugin_name)

    def getPrefs(self):
        return self._prefs_store

    def savePrefs(self, user_copy):
        self._prefs_store = user_copy
        self._prefs_store._commit()

    def launcher_version(self):
        return self._w.getversion()

    def epub_version(self):
        return self._w.getepubversion()

    def epub_is_standard(self):
        return self._w.epub_is_standard()

    @property
    def sigil_ui_lang(self):
        if self._w.sigil_ui_lang is None:
            return 'en'
        return self._w.sigil_ui_lang

    @property
    def sigil_spellcheck_lang(self):
        if self._w.sigil_spellcheck_lang is None:
            return 'en_US'
        return self._w.sigil_spellcheck_lang

# OPF Acess and Manipulation Routines

# toc and pagemap access routines

    def gettocid(self):
        '''returns the current manifest id as a unicode string for the toc.ncx Table of Contents'''
        return self._w.gettocid()

    def getpagemapid(self):
        '''returns the current manifest id as a unicode string for the page-map.xml (or None)'''
        return self._w.getpagemapid()

# nav access routines

    def getnavid(self):
        '''return self._w.getnavid()'''
        return self._w.getnavid()

# spine get/set and access routines

    def getspine(self):
        '''
        returns an ordered list of tuples (manifest_id, linear)\n
        manifest_id is a unicode string representing a specific file in the manifest\n
        linear is either "yes" or "no"
        '''
        # spine is an ordered list of tuples (id, linear)
        return self._w.getspine()

    def setspine(self, new_spine:list):
        '''
        sets the current spine order to new_spine\n
        where new_spine is an ordered list of tuples (manifest_id, linear)\n
        manifest_id is a unicode string representing a specific file\n
        linear is either "yes" or "no"
        '''
        # new_spine must be an ordered list of tuples (id, linear)
        self._w.setspine(new_spine)

    # New for epub3
    def getspine_epub3(self):
        '''return an ordered list of tuples (id, linear, properties)'''
        # spine is an ordered list of tuples (id, linear, properties)
        return self._w.getspine_epub3()

    # New for epub3
    def setspine_epub3(self, new_spine:list):
        '''set the spine to the ordered list of tuples (id, linear, properties (or None)'''
        # new_spine must be an ordered list of tuples (id, linear, properties (or None))
        self._w.setspine_epub3(new_spine)

    # Modified for epub3
    # Note: for prepend, set pos = 0
    #       for append, set pos = -1 or pos >= current length of spine
    def spine_insert_before(self, pos, spid, linear, properties=None):
        '''
        inserts the string manifest_id_to_insert immediately before given position in the spine\n
        positions start numbering at 0\n
        position = 0 will prepend to the spine\n
        position = -1 or position >= spine length will append\n
        linear is either "yes" or "no"
        '''
        self._w.spine_insert_before(pos, spid, linear, properties)

    def getspine_ppd(self):
        '''returns a unicode string indicating page-progression direction ("ltr", "rtl", None)'''
        # spine_ppd is utf-8 string of page direction (rtl, ltr, None)
        return self._w.getspine_ppd()

    def setspine_ppd(self, ppd:str):
        '''
        sets the spine page-progression-direction to the unicode string page-progression-direction\n
        allowable values are "ltr", "rtl" or None
        '''
        # new pagedirection string
        self._w.setspine_ppd(ppd)

    # New for epub3
    def setspine_idref_epub3_attributes(self, idref:str, linear:str, properties:str):
        '''set the spine with provided idref with linear and properties values'''
        self._w.setspine_idref_attributes(idref, linear, properties)


# guide get/set

    def getguide(self):
        '''
        returns the guide as an ordered list of tuples (type, title, href)\n
        where type (unicode string) is the guide type\n
        title (unicode string) is the associated guide title\n
        href (unicode string) is the associated guide target uri href\n
        '''
        # guide is an ordered list of tuples (type, title, href)
        return self._w.guide

    def setguide(self, new_guide:list):
        '''
        sets the guide to be new_guide where new_guide is an ordered list of tuples (type, title, href)\n
        type (unicode string) is the guide type\n
        title (unicode string) is the associated guide title\n
        href (unicode string) is the associated target uri href
        '''
        # new_guide must be an ordered list of tupes (type, title, href)
        self._w.setguide(new_guide)


# bindings get/set access routines

    # New for epub3
    def getbindings_epub3(self):
        '''
        bindings is an ordered list of tuples (media-type, handler)\n
        return self._w.getbindings_epub3()
        '''
        # bindings is an ordered list of tuples (media-type, handler)
        return self._w.getbindings_epub3()

    # New for epub3
    def setbindings_epub3(self, new_bindings):
        '''
        new_bindings is an ordered list of tuples (media-type, handler)\n
        self._w.setbindings_epub3(new_bindings)
        '''
        # new_bindings is an ordered list of tuples (media-type, handler)
        self._w.setbindings_epub3(new_bindings)

# metadata get/set

    def getmetadataxml(self):
        '''returns a unicode string of the metadata xml fragment from the OPF'''
        # returns a utf-8 encoded metadata xml fragement
        return self._w.getmetadataxml()

    def setmetadataxml(self, new_metadata:typing.Union[str,bytes]):
        '''
        sets the OPF metadata xml fragment to be new_metadataxml\n
        where new_metadataxml is a unicode string wrapped in its metadata start/end tags
        '''
        # new_metadata must be a metadata xml fragmment
        self._w.setmetadataxml(new_metadata)

# package tag get/set

    def getpackagetag(self):
        '''returns the starting package tag as a unicode string'''
        # returns a utf-8 encoded metadata xml fragement
        return self._w.getpackagetag()

    def setpackagetag(self, new_tag:str):
        '''sets the starting package tag to new_tag which is a unicode string'''
        # new_tag must be a xml package tag
        self._w.setpackagetag(new_tag)


# reading / writing / adding / deleting files in the opf manifest

    def readfile(self, id:str):
        '''
        returns the contents of the file with the provided manifest_id unicode string as binary data or unicode string as appropriate
        '''
        # returns the contents of the file with manifest id  (text files are utf-8 encoded)
        return self._w.readfile(id)

    def writefile(self, id:str, data:typing.Union[str,bytes]):
        '''writes the unicode text or binary data string to the file pointed to by the provided manifest_id string. If text, the file itself will be utf-8 encoded.'''
        # writes data to a currently existing file pointed to by the manifest id
        self._w.writefile(id, data)

    # Modified for epub3
    def addfile(self, uniqueid:str, basename:str, data:typing.Union[str,bytes], mime:str=None, properties:str=None, fallback:str=None, overlay:str=None):
        '''
        creates a new file and gives it the desired_unique_manifest_id string\n
        where basename is the desired name of the file with extension (no path added)\n
        data is either a string of binary data or a unicode text string\n
        if provided the file will be given the media-type provided by the mime-string, and if not provided the file extension is used to set the appropriate media-type\n
        to support epub3 manifests, properties, fallback, and media-overlay atributes can also be set.
        '''
        # creates a new file in the manifest with unique manifest id, basename, data, and mimetype
        self._w.addfile(uniqueid, basename, data, mime, properties, fallback, overlay)

    def deletefile(self, id:str):
        '''removes the file associated with that manifest id unicode string and removes any existing spine entries as well'''
        # removes the file associated with that manifest id, removes any existing spine entries as well
        self._w.deletefile(id)

    # New for epub3
    def set_manifest_epub3_attributes(self, id:str, properties:str=None, fallback:str=None, overlay:str=None):
        '''set the epub3 manifest properties, fallback, and media-overlay attributes for this manifest id'''
        # sets the epub3 manifest attrobutes for this manifest id
        self._w.set_manifest_epub3_attributes(id, properties, fallback, overlay)

# reading / writing / adding / deleting other ebook files that DO NOT exist in the opf manifest

    def readotherfile(self, book_href:str):
        '''returns the contents of the file pointed to by an href relative to the root directory of the ebook as unicode text or binary bytestring data'''
        # returns the contents of the file pointed to by the ebook href
        return self._w.readotherfile(book_href)

    def writeotherfile(self, book_href:str, data:typing.Union[str,bytes]):
        '''writes data (binary or unicode for text) to a currently existing file pointed to by the ebook href. If text, the file itself will be utf-8 encoded'''
        # writes data to a currently existing file pointed to by the ebook href
        self._w.writeotherfile(book_href, data)

    def addotherfile(self, book_href:str, data:typing.Union[str,bytes]):
        '''
        creates a new file with desired href (relative to the ebook root directory) with the supplied data.\n
        the path to the href will be automatically created\n
        data is a bytestring that is unicode for text and binary otherwise. If text, the resulting file itself will be utf-8 encoded\n
        '''
        # creates a new file with desired ebook href
        self._w.addotherfile(book_href, data)

    def deleteotherfile(self, book_href:str):
        '''
        deletes the file pointed to by the href (relative to the ebook root directory)
        '''
        # removes file pointed to by the ebook href
        self._w.deleteotherfile(book_href)


# iterators

    def text_iter(self):
        '''python iterator over all xhtml/html files: yields the tuple (manifest_id, OPF_href)'''
        # yields manifest id, href in spine order plus any non-spine items
        text_set = set([k for k, v in self._w.id_to_mime.items() if v == 'application/xhtml+xml'])
        for (id, linear, properties) in self._w.spine:
            if id in text_set:
                text_set -= set([id])
                href = self._w.id_to_href[id]
                yield id, href
        for id in text_set:
            href = self._w.id_to_href[id]
            yield id, href

    def css_iter(self):
        '''python iterator over all style sheets (css) files: yields the tuple (manifest_id, OPF_href)'''
        # yields manifest id, href
        for id in sorted(self._w.id_to_mime):
            mime = self._w.id_to_mime[id]
            if mime == 'text/css':
                href = self._w.id_to_href[id]
                yield id, href

    def image_iter(self):
        '''python iterator over all image files: yields the tuple (manifest_id, OPF_href, media-type)'''
        # yields manifest id, href, and mimetype
        for id in sorted(self._w.id_to_mime):
            mime = self._w.id_to_mime[id]
            if mime.startswith('image'):
                href = self._w.id_to_href[id]
                yield id, href, mime

    def font_iter(self):
        '''python iterator over all font files: yields the tuple (manifest_id, OPF_href, media-type)'''
        # yields manifest id, href, and mimetype
        for id in sorted(self._w.id_to_mime):
            mime = self._w.id_to_mime[id]
            if 'font-' in mime or 'truetype' in mime or 'opentype' in mime or mime.startswith('font/'):
                href = self._w.id_to_href[id]
                yield id, href, mime

    def manifest_iter(self):
        '''python iterator over all files in the OPF manifest: yields the tuple (manifest_id, OPF_href, media-type)'''
        # yields manifest id, href, and mimetype
        for id in sorted(self._w.id_to_mime):
            mime = self._w.id_to_mime[id]
            href = self._w.id_to_href[id]
            yield id, href, mime

    # New for epub3
    def manifest_epub3_iter(self):
        '''yields manifest id, href, media-type, properties, fallback, media-overlay'''
        # yields manifest id, href, mimetype, properties, fallback, media-overlay
        for id in sorted(self._w.id_to_mime):
            mime = self._w.id_to_mime[id]
            href = self._w.id_to_href[id]
            properties = self._w.id_to_props[id]
            fallback = self._w.id_to_fall[id]
            overlay = self._w.id_to_over[id]
            yield id, href, mime, properties, fallback, overlay

    def spine_iter(self):
        '''python iterator over all files in the OPF spine in order: yields the tuple (spine_idref, linear, OPF_href)'''
        # yields spine idref, linear(yes,no,None), href in spine order
        for (id, linear, properties) in self._w.spine:
            href = self._w.id_to_href[id]
            yield id, linear, href

    # New for epub3
    def spine_epub3_iter(self):
        '''yields spine idref, linear(yes, no, None), properties, and href in spine order'''
        # yields spine idref, linear(yes,no,None), properties, href in spine order
        for (id, linear, properties) in self._w.spine:
            href = self._w.id_to_href[id]
            yield id, linear, properties, href


    def guide_iter(self):
        '''
        python iterator over all entries in the OPF guide:\n
        yields the tuple (reference_type, title, OPF_href, manifest_id_of_OPF_ href)
        '''
        # yields guide reference type, title, href, and manifest id of href
        for (type, title, href) in self._w.guide:
            thref = href.split('#')[0]
            id = self._w.href_to_id.get(thref, None)
            yield type, title, href, id

    # New for epub3
    def bindings_epub3_iter(self):
        '''yields media-type handler in bindings order'''
        # yields media-type handler in bindings order
        for (mtype, handler) in self._w.bindings:
            handler_href = self._w.id_to_href[handler]
            yield mtype, handler, handler_href


    def media_iter(self):
        '''python iterator over all audio and video files: yields the tuple (manifest_id, OPF_href, media-type)'''
        # yields manifest, title, href, and manifest id of href
        for id in sorted(self._w.id_to_mime):
            mime = self._w.id_to_mime[id]
            if mime.startswith('audio') or mime.startswith('video'):
                href = self._w.id_to_href[id]
                yield id, href, mime

    def other_iter(self):
        '''python iterator over all files not in the Manifest: yields href from ebook root directory'''
        # yields otherid for each file not in the manifest
        for book_href in self._w.other:
            yield book_href

    def selected_iter(self):
        '''
        该函数在模拟Sigil插件环境下，默认选择全部 xhtml 文件。\n
        迭代元组(id_type, manifest_id)
        '''
        # yields id type ('other' or 'manifest') and id/otherid for each file selected in the BookBrowser
        '''
        for book_href in self._w.selected:
            id_type = 'other'
            id = book_href
            if book_href in self._w.bookpath_to_id:
                id_type = 'manifest'
                id = self._w.bookpath_to_id[book_href]
            yield id_type, id
        '''
        text_set = set([k for k, v in self._w.id_to_mime.items() if v == 'application/xhtml+xml'])
        for (id, linear, properties) in self._w.spine:
            if id in text_set:
                text_set -= set([id])
                href = self._w.id_to_href[id]
                yield id, href
        for id in text_set:
            href = self._w.id_to_href[id]
            yield "manifest",id

    # miscellaneous routines

    # build the current opf incorporating all changes to date and return it
    def get_opf(self):
        '''returns the current OPF as a unicode string'''
        return self._w.build_opf()

    # create your own current copy of all ebook contents in destintation directory
    def copy_book_contents_to(self, destdir):
        '''copies all ebook contents to the previous destination directory created by the user'''
        self._w.copy_book_contents_to(destdir)

    # get path to hunspell dll / library
    def get_hunspell_library_path(self):
        return self._w.get_hunspell_path()
    
    # get a list of the directories that contain Sigil's hunspell dictionaries
    def get_dictionary_dirs(self):
        '''get a list of the directories that contain Sigil's hunspell dictionaries'''
        return self._w.get_dictionary_dirs()

    # get status of epub file open inside of Sigil
    def get_epub_is_modified(self):
        '''get status of epub file open inside of Sigil'''
        return self._w.epub_isDirty

    # get path to currently open epub or an inside Sigil or empty string if unsaved
    def get_epub_filepath(self):
        '''get path to currently open epub or an inside Sigil or empty string if unsaved'''
        return self._w.epub_filepath


    # functions for converting from  manifest id to href, basename, mimetype etc
    def href_to_id(self, href, ow=None):
        '''given an OPF href, return the manifest id, if the href does not exist return ow'''
        return self._w.map_href_to_id(href, ow)

    def id_to_mime(self, id, ow=None):
        '''given a manifest id, return the media-type, if the manifest_id does not exist return ow'''
        return self._w.map_id_to_mime(id, ow)

    def basename_to_id(self, basename, ow=None):
        '''given a file's basename (with extension) return its manifest id, otherwise return ow'''
        return self._w.map_basename_to_id(basename, ow)

    def id_to_href(self, id, ow=None):
        '''given a manifest_id return its OPF href, otherwise return ow'''
        return self._w.map_id_to_href(id, ow)

    def href_to_basename(self, href, ow=None):
        '''given an OPF_href return the basename (with extension) of the file OPF, otherwise return ow'''
        if href is not None:
            return href.split('/')[-1]
        return ow

    # New for epub3
    def id_to_properties(self, id, ow=None):
        '''maps manifest id to its properties attribute'''
        return self._w.map_id_to_properties(id, ow)

    def id_to_fallback(self, id, ow=None):
        '''maps manifest id to its fallback attribute'''
        return self._w.map_id_to_fallback(id, ow)

    def id_to_overlay(self, id, ow=None):
        '''maps manifest id to its media-overlay attribute'''
        return self._w.map_id_to_overlay(id, ow)


    # New in Sigil 1.1
    # ----------------

    # returns "light" or "dark"
    def colorMode(self):
        '''returns "light" or "dark"'''
        return self._w.colorMode()

    # returns color as css or javascript hex color string #xxxxxx
    # acccepts the following color roles in a case insensitive manner:
    #    "Window", "Base", "Text", "Highlight", "HighlightedText"
    def color(self, role):
        '''
        returns color as css or javascript hex color string #xxxxxx \n
        acccepts the following color roles in a case insensitive manner:\n
        "Window", "Base", "Text", "Highlight", "HighlightedText" \n
        '''
        return self._w.color(role)


    # New in Sigil 1.0
    # ----------------

    # A book path (aka bookpath) is a unique relative path from the
    # ebook root to a specific file in the epub.  As a relative path meant
    # to be used in an href or src "link", it only uses forward slashes "/"
    # as path separators.  Since all files exist inside the
    # epub root (folder the epub was unzipped into), bookpaths will NEVER
    # have or use "./" or "../" ie they are in always in canonical form

    # For example under Sigil pre 1.0, all epubs were put into a standard
    # structure.  Under this standard structure book paths would look like
    # the following:
    #   OEBPS/content.opf
    #   OEBPS/toc.ncx
    #   OEBPS/Text/Section0001.xhtml
    #   OEBPS/Images/cover.jpg
    #

    # and src and hrefs always looked like the following:
    #    from Section0001.xhtml to Section0002.xhtml: ../Text/Section0002.xhtml
    #    from Section0001.xhtml to cover.jpg:         ../Images/cover.jpg
    #    from content.opf to Section0001.xhtml        Text/Section0001.xhtml
    #    from toc.ncx to Section0001.xhtml            Text/Section0001.xhtml

    # Under Sigil 1.0 and later, the original epub structure can be preserved
    # meaning that files like content.opf could be named package.opf, and be placed
    # almost anyplace inside the epub.  This is true for almost all files.

    # So to uniquely identify a file, you need to know the bookpath of the OPF
    # and the manifest href to the specific file, or the path from the epub
    # root to the file itself (ie. its bookpath)

    # so the Sigil plugin interface for Sigil 1.0 has been extended to allow
    # the plugin developer to more easily work with bookpaths, create links
    # between bookpaths, etc.

    # we will use the terms book_href (or bookhref) interchangeably
    # with bookpath with the following convention:
    #    - use book_href when working with "other" files outside the manifest
    #    - use bookpath when working with files in the opf manifest
    #    - use either when working with the OPF file as it is at the intersection

    # returns the bookpath/book_href to the opf file
    def get_opfbookpath(self):
        '''returns the bookpath/book_href to the opf file'''
        return self._w.get_opfbookpath()

    # returns the book path of the folder containing this bookpath
    def get_startingdir(self, bookpath):
        '''returns the book relative path to the folder containing this bookpath'''
        return self._w.get_startingdir(bookpath)

    # return a bookpath for the file pointed to by the href
    # from the specified bookpath starting directory
    def build_bookpath(self, href, starting_dir):
        '''return a bookpath for the file pointed to by the href from the specified bookpath starting directory'''
        return self._w.build_bookpath(href, starting_dir)

    # returns the href relative path from source bookpath to target bookpath
    def get_relativepath(self, from_bookpath, to_bookpath):
        '''returns the href relative path from source bookpath to the target bookpath'''
        return self._w.get_relativepath(from_bookpath, to_bookpath)

    # adds a new file to the *manifest* with the stated bookpath with the provided
    # uniqueid, data, (and mediatype if specified)
    def addbookpath(self, uniqueid, bookpath, data, mime=None):
        '''adds a new file to the *manifest* with the stated bookpath and with the provided uniqueid, data, (and media type if specified)'''
        return self._w.addbookpath(uniqueid, bookpath, data, mime)

    # functions for converting from  manifest id to bookpath and back
    def bookpath_to_id(self, bookpath, ow=None):
        '''
        looks up the provided bookpath and returns the corresponding manifest id\n
        if the bookpath does not exist in the OPF manifest, ow will be returned
        '''
        return self._w.map_bookpath_to_id(bookpath, ow)

    def id_to_bookpath(self, id, ow=None):
        '''
        looks up the provided manifest id and returns the corresponding bookpath of the file\n
        if the manifest id does not exist in the OPF manifest, ow will be returned
        '''
        return self._w.map_id_to_bookpath(id, ow)

    # valid groups: Text, Styles, Images, Fonts, Audio, Video, ncx, opf, Misc
    # returns a sorted folder list of ebook paths for a group
    def group_to_folders(self, group, ow=None):
        '''
        returns a sorted list of folders for the specified file type group\n
        valid groups: "Text", "Styles", "Images", "Fonts", "Audio", "Video", "ncx", "opf", and "Misc"\n
        the first book relative folder path in the list will be the default folder for that file type if more than one location has been used in the epub's layout
        '''
        return self._w.map_group_to_folders(group, ow)

    def mediatype_to_group(self, mediatype, ow=None):
        '''
        lookup the file type group based on a file's media type\n
        if the media type is not found, ow is returned
        '''
        return self._w.map_mediatype_to_group(mediatype, ow)

    
    # Newly Added to Support Plugins running in Automate Lists
    def using_automate(self):
        '''Newly Added to Support Plugins running in Automate Lists'''
        return self._w.using_automate

    def automate_parameter(self):
        '''Newly Added to Support Plugins running in Automate Lists'''
        return self._w.automate_parameter
    
    def save_as(self,save_path:str=""):
        '''
        将处理过的EPUB保存到指定路径（带文件名）。\n
        save_path\xa0\xa0\xa0\xa0指定保存路径，未指定时默认保存至同级OUTPUT目录下的同名EPUB文件。
        '''
        return self._w.save_as(save_path)

    def standardize_epub(self):
        '''重构EPUB为Sigil规范格式'''
        return self._w.standardize_epub()