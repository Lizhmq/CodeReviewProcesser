import os
import json
import random
import numpy as np
from cleaner import CodeCleaner, CommentCleaner
import logging

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



prcnt = 2500
repos = get_repos(prcnt)
logger.warning(f"Repo numbers: {len(repos)}")
logger.warning(f"Repo examples: {repos[:10]}")


datadir = "/home/v-zhuoli1/lzzz/reviewdata.bc"
outputdir = "/home/v-zhuoli1/lzzz/reviewdata.bc/final"

if not os.path.isdir(outputdir):
    os.mkdir(outputdir)
repos = get_repos(prcnt)

clsfiles = [repo2str(repodic, "cls") for repodic in repos]
genfiles = [repo2str(repodic, "gen") for repodic in repos]
cls_files = [os.path.join(datadir, f) for f in clsfiles if f.startswith("review_cls") and f.endswith(".jsonl")]
gen_files = [os.path.join(datadir, f) for f in genfiles if f.startswith("review_gen") and f.endswith(".jsonl")]
cls_files = [file for file in cls_files if os.path.isfile(file)]
gen_files = [file for file in gen_files if os.path.isfile(file)]
allfiles = cls_files + gen_files

clscnt, gencnt = 0, 0
pairs = []
for file in allfiles:
    try:
        pairs.append((file, open(file, "r"), cntline(open(file, "r"))))
    except:
        pass
    if len(pairs) % 100 == 0:
        logger.warning("Counted {} files".format(len(pairs)))
pairs = [pair for pair in pairs if pair[2] > 0]
pairs = list(sorted(pairs))
random.seed(2233)
random.shuffle(pairs)
logger.warning("Examples: " + str([p[0] for p in pairs[:3]]))
halfl = len(pairs) // 2

# If disk is not large enough to process the whole dataset (more than 300G),
#  process half of the dataset instead.
# pairs = pairs[:halfl]
# pairs = pairs[halfl:]


# save the data infomation, for later statistics
# run `python static.py` to read the data info.
outpairs = [(pair[0], pair[2]) for pair in pairs]
with open(os.path.join(outputdir, "statistics.json"), "w") as f:
    f.write(json.dumps(outpairs, indent=4))


lens = np.array([p[2] for p in pairs])
nchunks = 32 + 1
breakcnt = np.ceil(sum(lens) / nchunks)
logger.warning("Breakcnt: {}".format(breakcnt))
outlist = []
outidx = 0
# outidx = 27
outfile = "pretrain_"



codc = CodeCleaner()
comc = CommentCleaner()
while sum(lens) > 0:
    idx = np.random.choice(range(len(lens)), 1, p=lens/np.sum(lens))[0]
    lens[idx] -= 1
    file, fp, cnt = pairs[idx]
    repodic = str2repo(file)
    repo, lang = repodic["repo"], repodic["lang"]
    try:
        line = next(fp)
        dic = json.loads(line)
    except:
        logger.warning("JSON decoding error.")
        continue
    dic["proj"], dic["lang"] = repo, lang
    if "msg" not in dic or len(dic["msg"]) == 0:
        dic["msg"] = ""
    if dic["msg"] != "":
        comment = comc.clean(dic["msg"])
        if len(comment) > 0 and comment[0] == '<' and comment[-1] == '>':
            comment = ""
        dic["msg"] = comment
    code = codc.clean(dic["patch"])
    if len(code) > 0 and code[0] == '<' and code[-1] == '>':
        continue        # remove this patch
    if dic["msg"] != "":
        gencnt += 1
    else:
        clscnt += 1
    outlist.append(json.dumps(dic))
    if len(outlist) == breakcnt:
        with open(os.path.join(outputdir, outfile + str(outidx) + ".jsonl"), "w") as fp:
            fp.write("\n".join(outlist) + "\n")
        outlist = []
        outidx += 1
        logger.warning(f"{outidx} files written.")

with open(os.path.join(outputdir, outfile + str(outidx) + ".jsonl"), "w") as fp:
    fp.write("\n".join(outlist))
    
logger.warning(f"{outidx + 1} files written.\nDone.")
logger.warning(f"Clscnt: {clscnt}" + f"\tGencnt: {gencnt}")
