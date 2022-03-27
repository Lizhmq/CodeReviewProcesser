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

def get_repofilenames(minprcnt=2500):
    path = "/home/v-zhuoli1/lzzz/TopRepos/repos"
    files = os.listdir(path)
    files = [file for file in files if file.startswith("process_txt_")]
    retpaths = []
    for file in files:
        if int(file.split("_")[-1][:-4]) >= minprcnt:
            retpaths.append(os.path.join(path, file))
    return retpaths

def get_repos(minprcnt=2500):
    filenames = get_repofilenames(minprcnt)
    repos = []
    for filename in filenames:
        with open(filename, "r") as f:
            repos += [s.strip() for s in f.readlines()]
    repos = [{"repo": s.split(",")[0], "lang": s.split(",")[1]} for s in repos]
    return repos

def cntline(fp):
    cnt = 0
    while True:
        try:
            next(fp)
            cnt += 1
        except StopIteration:
            break
    return cnt


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
prcnt = 2500
repos = get_repos(prcnt)
logger.warning(f"Repo numbers: {len(repos)}")
logger.warning(f"Repo examples: {repos[:10]}")


datadir = "/home/v-zhuoli1/lzzz/reviewdata.bc"
outputdir = "/home/v-zhuoli1/lzzz/Processor/newdata"

if not os.path.isdir(outputdir):
    os.mkdir(outputdir)
repos = get_repos(prcnt)

clsfiles = [repo2str(repodic, "cls") for repodic in repos]
cls_files = [os.path.join(datadir, f) for f in clsfiles if f.startswith("review_cls") and f.endswith(".jsonl")]
cls_files = [file for file in cls_files if os.path.isfile(file)]
cls_files = list(sorted(cls_files))
sample_rates = 0.18
cls_files = random.choices(cls_files, k=int(len(cls_files)*sample_rates))
gen_files = [cls_files.replace("cls", "gen") for cls_files in cls_files]


outdata = []
codc = CodeCleaner()
comc = CommentCleaner()
breakcnt = 50000
chunkidx = 0
for clsfile, genfile in tqdm(zip(cls_files, gen_files)):
    repodic = str2repo(clsfile)
    repo, lang = repodic["repo"], repodic["lang"]
    with open(clsfile, "r") as f:
        for line in f:
            try:
                data = json.loads(line)
            except:
                logger.warning("JSON decoding error.")
                continue
            assert "y" in data
            if data["y"] == 1:
                continue
            data["msg"] = ""
            data["proj"], data["lang"] = repo, lang
            code = codc.clean(data["patch"])
            if len(code) > 0 and code[0] == '<' and code[-1] == '>':
                # remove this patch
                continue
            data["patch"] = code
            outdata.append(data)
    with open(genfile, "r") as f:
        for line in f:
            try:
                data = json.loads(line)
            except:
                logger.warning("JSON decoding error.")
                continue
            if "msg" not in data or len(data["msg"]) == 0:
                data["msg"] = ""
            if data["msg"] != "":
                comment = comc.clean(data["msg"])
                if len(comment) > 0 and comment[0] == '<' and comment[-1] == '>':
                    comment = ""
                data["msg"] = comment
            data["y"] = 1
            outdata.append(data)
    if len(outdata) > breakcnt:
        with open(os.path.join(outputdir, f"outtrain-{chunkidx}.jsonl"), "w") as f:
            for data in outdata:
                f.write(json.dumps(data) + "\n")
        outdata = []
        chunkidx += 1
    logger.warning(f"{repo} processed.")

with open(os.path.join(outputdir, f"outtrain-{chunkidx}.jsonl"), "w") as fp:
    for data in outdata:
        fp.write(json.dumps(data) + "\n")
