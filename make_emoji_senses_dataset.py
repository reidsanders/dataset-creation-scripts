#!/usr/bin/env python3

from copy import deepcopy
from functools import partial
from pathlib import Path
from tkinter import W
from PIL import Image
from tqdm import trange
import json
import typer
from pprint import pprint
import imgkit
import requests
import re
import base64
from torch.utils.data.dataset import random_split
import os
from tqdm import tqdm

app = typer.Typer()


@app.command()
def save_emoji(
    indexfile: str,
    outdir: str = "emoji-senses/",
    size: int = 256,
    maxexamples: int = 1e20,
    overwrite: bool = False,
):
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    info = []
    with open(indexfile, "r") as f:
        data = json.loads(f.read())
    for i, emoji in tqdm(enumerate(data), total=len(data)):
        try:
            urlmatches, imgtaglist = to_png(emoji)
            for i, (urlmatch, imgtag) in enumerate(zip(urlmatches, imgtaglist)):
                name = emoji["name"].replace(" ", "-")
                name = name.replace(":", "-")
                filename = f"{name}_{i}.png"
                outfile = Path(outdir) / Path(filename)
                if outfile.is_file() and not overwrite:
                    # Already exists, don't waste time
                    info.append(
                        {
                            "text": emoji["name"],
                            "filename": filename,
                            "providernum": i,
                            "url": str(urlmatch),
                            "metadata": emoji,
                            "imgtag": imgtag,
                        }
                    )
                    continue

                response = requests.get(urlmatch, stream=True)
                if response.status_code == 200:
                    with open(outfile, "wb") as f:
                        img = Image.open(response.raw)
                        img = img.resize((size, size), Image.LANCZOS)  # add args
                        img.save(f)
                        del response
                    info.append(
                        {
                            "text": emoji["name"],
                            "filename": filename,
                            "providernum": i,
                            "url": str(urlmatch),
                            "metadata": emoji,
                            "imgtag": imgtag,
                        }
                    )
                    for k, v in emoji["senses"].items():
                        for codes in v:
                            for code, descriptions in codes.items():
                                for description in descriptions:
                                    info.append(
                                        {
                                            "text": description,
                                            "filename": filename,
                                            "providernum": i,
                                            "url": str(urlmatch),
                                            "metadata": emoji,
                                            "imgtag": imgtag,
                                        }
                                    )
                if i > maxexamples:
                    break
            if i > maxexamples:
                break
        except Exception as detail:
            print(f"Error in emoji download:\n{detail}")
            pass

    jsonfile = Path(outdir) / Path("index.json")
    with open(jsonfile, "w+") as f:
        print(f"JSON outfile: {jsonfile}")
        # train, val = random_split(info, [len(info)-len(info)//20, len(info)//20])
        jsondata = json.dumps(
            {
                "data": info,
            }
        )
        f.write(jsondata)


def to_png(emoji, version=0):
    url = re.findall(r"http://.*/", emoji["definition"])[-1]
    data = requests.get(url).text
    html_search_string = r"<img.*alt=\".*{}.*height=\"120\"\>"  # Hacky height check to prevent smaller thumbnails being picked
    matchlist = re.findall(
        html_search_string.format(emoji["name"]), data, flags=re.IGNORECASE
    )
    urlmatches = [
        re.findall(r"\"https.*thumbs.*.png\"", match, flags=re.IGNORECASE)
        for match in matchlist
    ]
    cleanmatches = []
    for sublist in urlmatches:
        for urlmatch in sublist:
            cleanmatches.append(urlmatch)

    cleanmatches = [urlmatch.strip('"') for urlmatch in cleanmatches]
    # import ipdb; ipdb.set_trace()
    return cleanmatches, matchlist


class EmojiConverter:
    def __init__(self):
        self.data = requests.get(
            "https://unicode.org/emoji/charts/full-emoji-list.html"
        ).text
        self.skintones_data = requests.get(
            "https://unicode.org/emoji/charts/full-emoji-modifiers.html"
        ).text

    def to_base64_png(self, emoji, version=0):
        """For different versions, you can set version = 0 for ,"""
        html_search_string = (
            r"<img alt='{}' class='imga' src='data:image/png;base64,([^']+)'>"  #'
        )
        try:
            matchlist = re.findall(html_search_string.format(emoji), self.data)
        except Exception:
            matchlist = re.findall(
                html_search_string.format(emoji), self.skintones_data
            )
        return matchlist[version]


if __name__ == "__main__":
    app()
