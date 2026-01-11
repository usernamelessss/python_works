
import re

def run(bk):
    '''Your plugin entry.'''
    return 0

if __name__ == "__main__":
    from sigil_env import Ebook
    epub_src = "test.epub"
    bk = Ebook(epub_src)
    print("Is the Epub standard : ",bk.epub_is_standard())
    print("Standardizing epub......")
    bk.standardize_epub()
    print("Is the Epub standard : ",bk.epub_is_standard())
    run(bk)
    bk.save_as("test_repack.epub")