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


if not os.path.exists("tmpfscr"):
    os.mkdir("tmpfscr")

# extract one hunk diff
mmap = {}
print(f"Start create gen dataset for {repo}")
for dic in tqdm(filtered_dic):
    hunkdiff = dic["hunk_diff"]
    diff = dic["diff"]
    oldf = dic["oldf"]
    msg = dic["message"]
    open(f"tmpfscr/a-{lang}-{filerepo}.txt", "w").write(diff)
    open(f"tmpfscr/b-{lang}-{filerepo}.txt", "w").write(hunkdiff)
    kth = locate_kth_patch(hunkdiff, diff)
    # print(kth)
    ret = os.system(f"filterdiff --hunks={kth} tmpfscr/a-{lang}-{filerepo}.txt > tmpfscr/c-{lang}-{filerepo}.txt")
    if ret < 0:
        continue
    with open(f"tmpfscr/c-{lang}-{filerepo}.txt") as f:
        for i in range(4):      # drop 4 lines
            f.readline()
        patch = f.read()
    # open(f"old-{filerepo}.txt", "w").write(dic["newf"])
    # open(f"revpatch-{filerepo}.txt", "w").write(patch)
    # f = os.system(f"patch -R old-{filerepo}.txt revpatch-{filerepo}.txt")
    # if f < 0:
    #     continue
    if len(patch) == 0:
        continue
    key = get_key_from_patch(patch)
    if key in mmap:
        continue
    else:
        mmap[key] = (oldf, patch, msg)

os.system(f"rm tmpfscr/a-{lang}-{filerepo}.txt tmpfscr/b-{lang}-{filerepo}.txt tmpfscr/c-{lang}-{filerepo}.txt")

pairs = []
for key, value in mmap.items():
    oldf, patch, msg = value
    pairs.append({"oldf": oldf, "patch": patch, "msg": msg})
with open(f"reviews/review_gen_{lang}_{repo.replace('/', '-')}.json", "w") as f:
    json.dump(pairs, f)



