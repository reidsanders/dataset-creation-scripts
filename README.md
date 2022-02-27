# dataset-creation-scripts
Some scripts for creating or manipulating datasets. Mainly focuses on images for gan training.

install:
git clone and run
```sh
pip install -r requirements.txt
```

## Emoji Senses data
Scrapes all the emojis as images, and saves a json file with various

emoji sense information from https://www.kaggle.com/rtatman/emojinet

```sh
$ python make_emoji_senses_dataset.py --help
```
```
Usage: make_emoji_senses_dataset.py [OPTIONS] INDEXFILE

Arguments:
  INDEXFILE  [required]

Options:
  --outdir TEXT                   [default: emoji-senses/]
  --size INTEGER                  [default: 256]
  --maxexamples INTEGER           [default: 9999999999999999999]
  --overwrite / --no-overwrite    [default: no-overwrite]
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.
```

Example: 
```sh
python make_emoji_senses_dataset.py datasets/emojis.json --outdir processed/emoji-senses/
  0%|▏                                                       | 8/2389 [00:05<29:10,  1.36it/s]
```



## Drawtext 
Turns text into images. 

Text mode splits up a text dataset and render the text to images. It tries to split on sentence first. 


You can check usage with help:
```sh
python drawtext.py -h
```
```
usage: drawtext.py [-h] [--dirpath DIRPATH] [--out OUT] [--split SPLIT] [--align ALIGN] [--font_size FONT_SIZE]
                   [--size SIZE] [--mode MODE]

boilerplate arg parser

optional arguments:
  -h, --help            show this help message and exit
  --dirpath DIRPATH     input dir
  --out OUT             out dir
  --split SPLIT         sentence, word
  --align ALIGN         left, upperleft, center
  --font_size FONT_SIZE
                        font size
  --size SIZE           size of output image
  --mode MODE           'text' or 'font'
```

```sh
python drawtext.py --out datasets/out/ --align left --size 256,256 --mode text --dirpath datasets/directory_with_texts/
```

Font mode renders characters with every font. You would need to download a large amount of fonts to create reasonable training data.

See also [danbooru-utility](https://github.com/reidsanders/danbooru-utility) for working on gwern's danbooru dataset, and https://github.com/reidsanders/v-diffusion-pytorch for training code based on kcrawson's work.

### Improvements
These are pretty hacky scripts since they are run a few times to create a dataset. Adding multiprocessing would speed them up tremendously.
