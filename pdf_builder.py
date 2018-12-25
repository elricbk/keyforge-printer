#!/usr/bin/env python3
# coding: utf-8

# TODO: replace with smth. builtin
from bs4 import BeautifulSoup

import tempfile
import os
from multiprocessing import Pool
import glob
import urllib.request
import subprocess

URL_EXAMPLE = "https://www.keyforgegame.com/deck-details/f52ef95f-5ddb-463a-91c5-0dcdd0ed4b14"

CARDS_PATH = "./cards/"
CONVERT_PATH = '/usr/local/bin/convert'
MONTAGE_PATH = '/usr/local/bin/montage'
OUTPUT_FILE = "./result.pdf"


# TODO: build crop marks file in runtime
CROP_MARKS_FILE = "./misc/crop_marks_full.png"
FILE_PATTERN = "[0-9][0-9][0-9]*"
USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) ' +
    'AppleWebKit/537.36 (KHTML, like Gecko) ' +
    'Chrome/35.0.1916.47 Safari/537.36'
)


def rm(fname):
    os.remove(fname)


def montage(*params):
    args = [MONTAGE_PATH]
    args.extend(params)
    subprocess.check_output(args, stderr=subprocess.STDOUT)


def convert(*params):
    args = [CONVERT_PATH]
    args.extend(params)
    subprocess.check_output(args, stderr=subprocess.STDOUT)


def load_image_map():
    images = {}
    for fname in glob.glob(os.path.join(CARDS_PATH, FILE_PATTERN)):
        fid = os.path.basename(fname)[:3]
        images[int(fid)] = fname
    return images


def get_card_list(url):
    req = urllib.request.Request(
        url,
        data=None,
        headers={ 'User-Agent': USER_AGENT }
    )
    response = urllib.request.urlopen(req).read()
    soup = BeautifulSoup(response, features="html.parser")
    return list(map(
        lambda it: int(it.text),
        soup.find_all("span", "card-table__deck-card-number")
    ))


def get_temp_fname():
    with tempfile.NamedTemporaryFile(suffix='.png') as f:
        return f.name


def build_page(page_cards):
    assert len(page_cards) == 9, "Page should contain 9 cards"
    
    # TODO: replace `montage` by `convert`
    PREFIX = ["-geometry", "+0+0", "-tile", "3x3"]
    fname = get_temp_fname()
    params = PREFIX + list(page_cards) + [fname]
    montage(*params)
    
    A4_SIZE = "2480x3508"
    BORDERED_SIZE = "2274x3174-12-12"
    JPEG_QUALITY = "94"
    convert_params = [
        "-size", A4_SIZE, "xc:white",
        "(",
            fname, CROP_MARKS_FILE, "-gravity", "center", "-composite",
            "(",
                "-clone", "0",
                "-set", "option:distort:viewport", BORDERED_SIZE,
                "-virtual-pixel", "mirror",
                "-distort", "SRT", "0,0 1,1 0",
            ")",
            "(", "-clone", "0", ")",
            "-delete", "0",
            "-gravity", "center",
            "-compose", "over",
            "-composite",
            "+repage",
        ")",
        "-gravity", "center",
        "-composite",
        "-quality", JPEG_QUALITY,
        fname + ".jpg"
    ]
    convert(*convert_params)
    rm(fname)
    return fname + ".jpg"


def build_pdf(card_list):
    assert len(card_list) == 36, "Deck should consist of 36 cards"
    fs = []
    # TODO: add card backs
    with Pool() as p:
        fs = list(p.map(build_page, zip(*[iter(card_list)]*9)))
    convert(*(fs + [OUTPUT_FILE]))
    for f in fs:
        rm(f)


def main():
    # TODO: add logging
    image_map = load_image_map()
    deck = get_card_list(URL_EXAMPLE)
    deck_images = list(map(lambda it: image_map[it], deck))
    build_pdf(deck_images)


if __name__ == "__main__":
    main()

