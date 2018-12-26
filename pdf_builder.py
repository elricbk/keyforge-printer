#!/usr/bin/env python3
# coding: utf-8

import tempfile
import os
from multiprocessing import Pool
import glob
import urllib.request
import subprocess
import html.parser
from functools import partial


URL_EXAMPLE = "https://www.keyforgegame.com/deck-details/f52ef95f-5ddb-463a-91c5-0dcdd0ed4b14"

CARDS_PATH = "./cards/"
CONVERT_PATH = '/usr/local/bin/convert'
MONTAGE_PATH = '/usr/local/bin/montage'
OUTPUT_FILE = "./result.pdf"


FILE_PATTERN = "[0-9][0-9][0-9]*"
USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) ' +
    'AppleWebKit/537.36 (KHTML, like Gecko) ' +
    'Chrome/35.0.1916.47 Safari/537.36'
)
DEFAULT_CROP_MARK_LENGTH = 24
DEFAULT_CROP_MARK_WIDTH = 2


class HTMLParser(html.parser.HTMLParser):
    def __init__(self):
        super(HTMLParser, self).__init__()
        self.cards = []

    def handle_starttag(self, tag, attrs):
        NUMBER_CLASS = "card-table__deck-card-number"
        self.in_card_number_span = (
            (tag == 'span') and
            ("class", NUMBER_CLASS) in attrs
        )

    def handle_endtag(self, tag):
        if self.in_card_number_span and tag == 'span':
            self.in_card_number_span = False

    def handle_data(self, data):
        if self.in_card_number_span:
            self.cards.append(int(data))


def rm(fname):
    os.remove(fname)


def montage(*params):
    args = [MONTAGE_PATH]
    args.extend(params)
    subprocess.check_output(args, stderr=subprocess.STDOUT)


def convert(*params):
    args = [CONVERT_PATH]
    args.extend(params)
    try:
        subprocess.check_output(args, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(e.output)
        raise


def load_image_map():
    images = {}
    for fname in glob.glob(os.path.join(CARDS_PATH, FILE_PATTERN)):
        fid = os.path.basename(fname)[:3]
        images[int(fid)] = fname
    return images


def get_deck_page(url):
    req = urllib.request.Request(
        url,
        data=None,
        headers={ 'User-Agent': USER_AGENT }
    )
    return urllib.request.urlopen(req).read().decode('utf-8')


def get_card_list(text):
    parser = HTMLParser()
    parser.feed(text)
    return parser.cards


def get_temp_fname():
    with tempfile.NamedTemporaryFile(suffix='.png') as f:
        return f.name


def build_page(crop_marks_file, page_cards):
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
            fname, crop_marks_file, "-gravity", "center", "-composite",
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


def build_crop_marks(w, h):
    l = DEFAULT_CROP_MARK_LENGTH
    crop_file_name = get_temp_fname()
    convert(
        "(",
            "-size", f"{w}x{h}",
            "xc:none",
            "-fill", "red",
            "-strokewidth", str(DEFAULT_CROP_MARK_WIDTH),
            "-draw", (
                f"line 0,0 0,{l} " +
                f"line 0,0 {l},0 " +
                f"line 0,{h - 1} 0,{h - l} " +
                f"line 0,{h - 1} {l},{h - 1} " +
                f"line {w - 1},0 {w - 1},{l} " +
                f"line {w - 1},0 {w - l},0 " +
                f"line {w - 1},{h - 1} {w - l},{h - 1} " +
                f"line {w - 1},{h - 1} {w - 1},{h - l}"
            ),
        ")",
        "-duplicate", "2", "+append",
        "-duplicate", "2", "-append",
        "+repage",
        crop_file_name
    )
    return crop_file_name


def build_pdf(card_list):
    assert len(card_list) == 36, "Deck should consist of 36 cards"
    crop_marks_file = build_crop_marks(750, 1050)
    fs = []
    # TODO: add card backs
    with Pool() as p:
        fs = list(p.map(
            partial(build_page, crop_marks_file),
            zip(*[iter(card_list)]*9)
        ))
    convert(*(fs + [OUTPUT_FILE]))
    for f in fs:
        rm(f)
    rm(crop_marks_file)


def main():
    # TODO: add logging
    image_map = load_image_map()
    html = get_deck_page(URL_EXAMPLE)
    deck = get_card_list(html)
    deck_images = list(map(lambda it: image_map[it], deck))
    build_pdf(deck_images)


if __name__ == "__main__":
    main()

