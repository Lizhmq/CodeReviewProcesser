import os, sys, time
import logging
import pprint
import requests
from tqdm import tqdm
from utils import get_cursor, get_all, get_from_attr, gen_dic, findkth
pprint = pprint.PrettyPrinter(indent=4).pprint

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(stream=sys.stdout, format=FORMAT)
logger = logging.getLogger("filepuller")


user, password = "FAREAST.v-zhuoli1", "passward"
db = "etcr"
repo = "elastic/elasticsearch"
token = "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"


conn, cur = get_cursor(db, user, password)
data = cur.execute("SELECT a.id, a.hunk_diff, a.message, a.created_at, b.diff, b.newf FROM comment a JOIN comment_file_pair b ON a.id = b.id;")
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


# extract one hunk diff
pairs = []
for dic in filtered_dic:
    hunkdiff = dic["hunk_diff"]
    diff = dic["diff"]
    open("a.txt", "w").write(diff)
    open("b.txt", "w").write(hunkdiff)
    kth = locate_kth_patch(hunkdiff, diff)
    print(kth)
    os.system(f"filterdiff --hunks={kth} a.txt > c.txt")
    with open("c.txt") as f:
        for i in range(4):      # drop 4 lines
            f.readline()
        patch = f.read()
    open("old.txt", "w").write(dic["newf"])
    open("revpatch.txt", "w").write(patch)
    f = os.system("patch -R old.txt revpatch.txt")
    if f < 0:
        continue
    pairs.append({"patch": patch, "msg": dic["message"]})

import json
with open("review_gen.json", "w") as f:
    json.dump(pairs, f)



