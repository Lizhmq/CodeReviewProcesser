import os
import json
import random
import numpy as np
from cleaner import CodeCleaner, CommentCleaner
import logging
from tqdm import tqdm

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def str2repo(s):
    s = s.split("/")[-1]    # get filename
    tmplist = s.split("_")
    tmplist[-1] = tmplist[-1][:-6]
    type = tmplist[1]
    lang = tmplist[2]
    repo = "_".join(tmplist[3:])
    return {"repo": repo, "lang": lang, "type": type}

def repo2str(repodic, type):
    return "review_{}_{}_{}.jsonl".format(type, repodic["lang"], repodic["repo"].replace("/", "-"))


random.seed(2233)


datadir = "/home/v-zhuoli1/wspace/CodeReviewProcesser/reviews"
outputdir = "/home/v-zhuoli1/lzzz/Processor/data"
files = list(sorted(os.listdir(datadir)))
files = [os.path.join(datadir, f) for f in files if f.startswith("review_cls") and f.endswith(".jsonl")]
files = [file for file in files if os.path.isfile(file)]
logger.warning(f"Repo numbers: {len(files)}")
logger.warning(f"Repo examples: {files[:10]}")
if not os.path.isdir(outputdir):
    os.mkdir(outputdir)



outdata = []
codc = CodeCleaner()
comc = CommentCleaner()
for file in tqdm(files):
    repodic = str2repo(file)
    repo, lang = repodic["repo"], repodic["lang"]
    with open(file, "r") as f:
        for line in f:
            try:
                data = json.loads(line)
            except:
                logger.warning("JSON decoding error.")
                continue
            if "msg" not in data:
                data["msg"] = ""
            if "y" not in data:
                data["y"] = 0
            data["proj"], data["lang"] = repo, lang
            code = codc.clean(data["patch"])
            if len(code) > 0 and code[0] == '<' and code[-1] == '>':
                continue    # remove this patch
            data["patch"] = code
            if data["msg"] != "":
                comment = comc.clean(data["msg"])
                if len(comment) > 0 and comment[0] == '<' and comment[-1] == '>':
                    comment = ""
                data["msg"] = comment
                data["y"] = 1
            outdata.append(data)
    logger.warning(f"{repo} processed.")

with open(os.path.join(outputdir, "outtest.jsonl"), "w") as fp:
    for data in outdata:
        fp.write(json.dumps(data) + "\n")
