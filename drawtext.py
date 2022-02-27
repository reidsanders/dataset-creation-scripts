#!/usr/bin/python

### Import libraries
import sys
import os
import argparse
import time
from wand.color import Color
from wand.image import Image
from wand.drawing import Drawing
from wand.compat import nested
import wand
import pickle
import json
from tqdm import tqdm
from textwrap import wrap

def str2bool(v):
    """Converts strings to appropriate bool, for argparse."""
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def get_args(arg_input):
    """Takes args input and returns them as a argparse parser

    Parameters
    -------------

    arg_input : list, shape (n_nargs,)
        contains list of arguments passed to function

    Returns
    -------------

    args : namespace
        contains namespace with keys and values for each parser argument

    """
    parser = argparse.ArgumentParser(
        description='boilerplate arg parser'
    )
    parser.add_argument(
        '--dirpath',
        type=str,
        default='input/',
        help="input dir"
    )
    parser.add_argument(
        '--out',
        type=str,
        default='out/',
        help="out dir"
    )
    parser.add_argument(
        '--split',
        type=str,
        default='sentence',
        help="sentence, word"
    )
    parser.add_argument(
        '--align',
        type=str,
        default='upperleft',
        help="left, upperleft, center"
    )
    parser.add_argument(
        '--font_size',
        type=int,
        default=24,
        help="font size"
    )
    parser.add_argument(
        '--size',
        type=lambda s: [int(item) for item in s.split(',')],
        default='128,128',
        help="size of output image"
    )
    parser.add_argument(
        '--mode',
        type=str,
        default='text',
        help="'text' or 'font'"
    )

    args = parser.parse_args(arg_input)
    return args

def draw_text(text,font,outfile,size=[64,64],align='center',font_size=30.0):
    with Drawing() as draw:
        with Image(width=size[0], height=size[1], background=Color('white')) as img:
            try:
                draw.font = font
                draw.font_size = font_size
                draw.push()
                draw.fill_color = Color('hsl(0%, 0%, 0%)')
                try:
                    mutable_message = word_wrap(img,
                                                draw,
                                                text,
                                                size[0]-10,
                                                size[1]-10)
                except RuntimeError as detail:
                    print(f"Error in word_wrap: {detail}")
                    return False

                if align == 'center':
                    draw.text(int(img.width/2)-font_size//4,int(img.height/2)+font_size//4, mutable_message)
                elif align == 'left':
                    draw.text(font_size//4,int(img.height/2)+font_size//4, mutable_message)
                elif align == 'upperleft':
                    draw.text(10,20, mutable_message)
                else:
                    draw.text(0,0, text)
                draw.pop()
                draw(img)
                img.save(filename=outfile)
                print(f"Saving file {outfile}")
                return True
            except wand.exceptions.TypeError as detail:
                print(f"Wand Exception: {detail}")
                return False
    return False

def split_on_sentence(data):
    from nltk.tokenize import sent_tokenize, word_tokenize
    tokenized = sent_tokenize(data)
    new_tokenized = []
    for sent in tokenized:
            #print(sent)
            done = False
            while True:
                if len(sent) < 5:
                    break
                new_tokenized.append(sent[:65])
                sent = sent[65:]

    return new_tokenized

            
def split_on_word(filepath):
    from nltk.tokenize import sent_tokenize, word_tokenize
    fp = open(filepath)
    data = fp.read()
    tokenized = word_tokenize(data)
    #print(tokenized)
    return tokenized


def create_char_dataset(args):
    char_options = '0123456789abcdefghijklmnopqrstwxyzABCDEFGHIJKLMNOPQRSTWXYZ'
    start_time = time.time()
    i = 0
    info = []
    for text in char_options:
        for root, dirs, files in os.walk('/home/rs/media/game-assets/fonts/10000-fonts-combined'):
            for (i, font_file) in enumerate(files):
                font = os.path.join(root,font_file)
                fontname = ''.join(c for c in os.path.splitext(font_file)[0] if c.isalnum())
                outfile = f"{fontname}_{text}_{i}.png"
                outpath = os.path.join(args.out,outfile)
                drawsuccess = draw_text(text,font,outpath,size=args.size,align=args.align,font_size=args.font_size)
                if drawsuccess:
                    info.append(
                        {
                            "text": text,
                            "filename": outfile,
                            "font": font_file,
                        }
                    )

    jsonfile = os.path.join(args.out, "index.json")
    with open(jsonfile, "w+") as f:
        print(f"JSON outfile: {jsonfile}")
        jsondata = json.dumps(
            {
                "data": info,
                # Add other metadata here
            }
        )
        f.write(jsondata)

def create_text_dataset(args,data):
    font = '/home/rs/.fonts/DroidSans.ttf'
    start_time = time.time()
    i = 0
    text_img_pairs = []

    for text in tqdm(data):
        name = ''.join(c for c in text if c.isalnum())
        name = ''.join([ch if ch != ' ' else '_' for ch in name])
        outfile = name+'-'+str(i)+".png"
        outpath = os.path.join(args.out,outfile)
        try:
            drawsuccess = draw_text(text,font,outpath,size=args.size,align=args.align,font_size=args.font_size)
            if drawsuccess:
                text_img_pairs.append([text, outfile])
        except Exception as detail:
            print(f"Error in draw_text: {detail}")
            continue
        i += 1
    jsonfile = os.path.join(args.out, "index.json")
    with open(jsonfile, "w+") as f:
        print(f"JSON outfile: {jsonfile}")
        print(f"saving dump {text_img_pairs}")
        jsondata = json.dumps(
            {
                "data": text_img_pairs,
                "font": font,
            }
        )
        f.write(jsondata)
        #if i > 10:
            #break

def word_wrap(image, ctx, text, roi_width, roi_height):
    """Break long text to multiple lines, and reduce point size
    until all text fits within a bounding box."""
    mutable_message = text
    iteration_attempts = 100

    def eval_metrics(txt):
        """Quick helper function to calculate width/height of text."""
        metrics = ctx.get_font_metrics(image, txt, True)
        return (metrics.text_width, metrics.text_height)

    def shrink_text():
        """Reduce point-size & restore original text"""
        ctx.font_size = ctx.font_size - 1
        mutable_message = text

    while ctx.font_size > 0 and iteration_attempts:
        iteration_attempts -= 1
        width, height = eval_metrics(mutable_message)
        if height > roi_height:
            shrink_text()
        elif width > roi_width:
            columns = len(mutable_message)
            while columns > 1:
                columns -= 1
                mutable_message = '\n'.join(wrap(mutable_message, columns))
                wrapped_width, _ = eval_metrics(mutable_message)
                if wrapped_width <= roi_width:
                    break
            if columns < 1:
                shrink_text()
        else:
            break
    if iteration_attempts < 1:
        raise RuntimeError("Unable to calculate word_wrap for " + text)
    return mutable_message




def main(args=None):
    if args == None:
        arg_input = sys.argv[1:]
        args = get_args(arg_input)
    if not os.path.exists(args.out):
        os.makedirs(args.out)
    if args.mode == "char":
        create_char_dataset(args)
    elif args.mode == "text":
        processed_data = []
        for root, dirs, files in os.walk(args.dirpath):
            for f in files:
                try:
                    fp = open(os.path.join(root,f))
                    data = fp.read()
                    data = data.replace("\r\n", " ")
                    data = data.replace('\n',' ')
                    data = data.replace("\r", " ")
                    print(data)
                except Exception as detail:
                    print(detail)
                    continue

                if args.split == 'word':
                    data = split_on_word(data)
                else:
                    data = split_on_sentence(data)
                processed_data += data
        create_text_dataset(args,processed_data)
    else:
        raise RuntimeError("invalid mode")

if __name__ == '__main__':
    main()

