import os, sys, time
import logging
import json
import pprint
import argparse
import requests
from tqdm import tqdm
from utils import get_cursor, get_all, get_from_attr, gen_dic, findkth
pprint = pprint.PrettyPrinter(indent=4).pprint

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(stream=sys.stdout, format=FORMAT)
logger = logging.getLogger("filepuller")


parser = argparse.ArgumentParser()
parser.add_argument("--db", default=None, type=str, required=True)
parser.add_argument("--repo", default=None, type=str, required=True)
parser.add_argument("--lang", default=None, type=str, required=True)
parser.add_argument("--token", default=None, type=str, required=True)
args = parser.parse_args()

user, password = "FAREAST.v-zhuoli1", "passward"
db, repo, lang, token = args.db, args.repo, args.lang, args.token
filerepo = repo.replace("/", '-')
token = args.token


conn, cur = get_cursor(db, user, password)
data = cur.execute("SELECT a.id, a.hunk_diff, a.message, a.created_at, b.oldf, b.diff, b.newf FROM comment a JOIN comment_file_pair b ON a.id = b.id;")
data = data.fetchall()
dics = gen_dic(cur.description, data)
dics = sorted(dics, key=lambda dic: dic["created_at"])
# len(dics)

# keep the first comment for each hunk diff
s = set()
filtered_dic = []
for dic in dics:
    if dic["hunk_diff"] in s:
        continue
    else:
        s.add(dic["hunk_diff"])
        filtered_dic.append(dic)
# len(filtered_dic)


def locate_kth_patch(hunkdiff, diff):
    adiff = hunkdiff.replace('\r', '')
    newlineidx = adiff.find("\n")
    if newlineidx == -1:
        newlineidx = 0
    # only check first 10 lines
    truncidx = findkth(adiff, "\n", 10)    # if diff hunk less than 10 lines, it's ok to be -1
    bdiff = adiff[newlineidx:truncidx]
    idx = diff.find(bdiff)
    count = diff[:idx].count("@@") // 2
    return count

def get_key_from_patch(s):
    '''
        Remove the frist line.  "@@ --, ++ @@"
    '''
    idx = s.find("\n")
    if idx == -1:
        idx = 0
    return s[idx:]


if not os.path.exists("/home/v-zhuoli1"):
    os.mkdir("/home/v-zhuoli1")


print(f"Start create cls dataset for {repo}")
# extract one hunk diff

mmap = {}
for dic in tqdm(filtered_dic):
    hunkdiff = dic["hunk_diff"]
    diff = dic["diff"]
    oldf = dic["oldf"]
    cmtid = dic["id"]
    kth = locate_kth_patch(hunkdiff, diff)
    open(f"/home/v-zhuoli1/diff-{lang}-{filerepo}.txt", "w").write(diff)
    hunk_cnts = diff.count("@@") // 2
    for i in range(1, hunk_cnts + 1):
        ret = os.system(f"filterdiff --hunks={i} /home/v-zhuoli1/diff-{lang}-{filerepo}.txt > /home/v-zhuoli1/hunk-{lang}-{filerepo}.txt")
        if ret < 0:
            continue
        with open(f"/home/v-zhuoli1/hunk-{lang}-{filerepo}.txt") as f:
            for __ in range(4):      # drop 4 lines
                f.readline()
            patch = f.read()
        if len(patch) == 0:
            continue
        if i == kth:
            y = 1
        else:
            y = 0
        key = get_key_from_patch(patch)
        if key in mmap:
            stored_y, stored_patch, stored_file, stored_idx, stored_cmtid = mmap[key]
            if y == 1 and stored_y == 0:
                mmap[key] = (y, patch, oldf, i, cmtid)
        else:
            mmap[key] = (y, patch, oldf, i, cmtid)
# print(sum(m.values()))
os.system(f"rm /home/v-zhuoli1/diff-{lang}-{filerepo}.txt /home/v-zhuoli1/hunk-{lang}-{filerepo}.txt")
    
pairs = []
for key, value in mmap.items():
    y, patch, oldf, idx, cmtid = value
    pairs.append({"patch": patch, "y": y, "oldf": oldf, "idx": idx, "id": cmtid})

with open(f"reviews/review_cls_{lang}_{filerepo}.json", "w") as f:
    json.dump(pairs, f)



