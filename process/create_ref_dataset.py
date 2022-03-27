import os, sys, time
import re
import logging
import pprint
import requests
import json
import argparse
from tqdm import tqdm
from utils import get_cursor, get_all, get_from_attr, write_jsonl, findkth
pprint = pprint.PrettyPrinter(indent=4).pprint

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(stream=sys.stdout, format=FORMAT)
logger = logging.getLogger("filepuller")
parser = argparse.ArgumentParser()
parser.add_argument("--db", default=None, type=str, required=True)
parser.add_argument("--repo", default=None, type=str, required=True)
parser.add_argument("--lang", default=None, type=str, required=True)
parser.add_argument("--token", default=None, type=str, required=True)
parser.add_argument("--ends", default=None, type=str, required=True)
parser.add_argument("--tmppath", default=None, type=str, required=True)
parser.add_argument("--outpath", default=None, type=str, required=True)
args = parser.parse_args()


def locate_kth_patch_reverse(hunkdiff, diff):
    hunkdiff = hunkdiff[::-1]
    adiff = hunkdiff.replace('\r', '')
    newlineidx = adiff.find("\n")
    if newlineidx == -1:
        newlineidx = 0
    # only check first 10 lines
    truncidx = findkth(adiff, "\n", 10)    # if diff hunk less than 10 lines, it's ok to be -1
    bdiff = adiff[newlineidx:truncidx]
    bdiff = bdiff[::-1]
    idx = diff.find(bdiff)
    count = diff[:idx].count("@@") // 2
    return count



def main():
    user, password = "FAREAST.v-zhuoli1", "passward"
    db, repo, lang, token = args.db, args.repo, args.lang, args.token
    logger.warning(f"Start repo: {db}.")
    tmppath, outpath = args.tmppath, args.outpath
    ends = args.ends
    filerepo = repo.replace("/", '-')
    conn, cur = get_cursor(db, user, password)

    if not os.path.exists(f"{tmppath}"):
        os.mkdir(f"{tmppath}")

    headers = {"Authorization": f"token {token}"}
    not_found = ['400: Invalid request', '404: Not Found']

    data = []

    FULLPRS = get_all(cur, "pull_request")
    for pr in FULLPRS:
        prid = pr["id"]
        allcmts = get_from_attr(cur, "comment", "pull_request_id", prid)
        allcmts = [cmt for cmt in allcmts if cmt["hunk_file"] and cmt["hunk_file"].endswith(ends)]
        allcmts = sorted(allcmts, key=lambda dic: dic["created_at"])
        allcommits = get_from_attr(cur, "commit", "pull_request_id", prid)
        allcommits = sorted(allcommits, key=lambda commit: commit["created_at"])
        if len(allcmts) <= 0 or len(allcommits) <= 0:
            continue
        for cmtidx in range(len(allcmts)):
            patchnum = 0
            comment = allcmts[cmtidx]
            comment_time = comment['created_at']
            file_path = comment["hunk_file"]
            commit_id = comment["commit_id"]
            comment_id = comment["id"]
            commit_fb_id = comment["commit_fallback_id"]
            author = comment["author"]
            allcommits = [commit for commit in allcommits if commit["author"] != author]
            # comment and commit author are different
            if len(allcommits) == 0:
                continue
            if not commit_id and commit_fb_id:
                commit_id = commit_fb_id
            if commit_id:
                firstidx = 0
                while firstidx < len(allcommits) and allcommits[firstidx]["id"] != commit_id:
                    firstidx += 1
                if firstidx < len(allcommits):
                    commit = allcommits[firstidx]
                else:
                    continue
            else:
                continue
            # find old patch
            first_commit = allcommits[0]
            first_hashv_b = first_commit["hash_parent"]
            hashv = commit["hash"]
            try:
                prevurl = f"https://raw.githubusercontent.com/{repo}/{first_hashv_b}/{file_path}"
                oldurl = f"https://raw.githubusercontent.com/{repo}/{hashv}/{file_path}"
                prev_contents = requests.get(prevurl, headers=headers).text
                old_contents = requests.get(oldurl, headers=headers).text
                if prev_contents in not_found:
                    prev_contents = ""
                if old_contents in not_found:
                    continue
            except Exception as e:
                continue
            open(f"{tmppath}/b-{lang}-{filerepo}.txt", "w").write(old_contents)
            secondidx = firstidx + 1
            while secondidx < len(allcommits) and allcommits[secondidx]["created_at"] < comment_time:
                secondidx += 1
            cmtgot = False
            for nextidx in range(secondidx, min(len(allcommits), secondidx + 10)):
                nexthashv = allcommits[nextidx]["hash"]
                try:
                    newurl = f"https://raw.githubusercontent.com/{repo}/{nexthashv}/{file_path}"
                    new_contents = requests.get(newurl, headers=headers).text
                    if new_contents in not_found:
                        continue
                except:
                    logger.warning("Error during fetching files.")
                    continue
                open(f"{tmppath}/a-{lang}-{filerepo}.txt", "w").write(old_contents)
                open(f"{tmppath}/b-{lang}-{filerepo}.txt", "w").write(new_contents)
                os.system(f"git diff --no-index {tmppath}/a-{lang}-{filerepo}.txt {tmppath}/b-{lang}-{filerepo}.txt > {tmppath}/diff-{lang}-{filerepo}.txt")
                diff = open(f"{tmppath}/diff-{lang}-{filerepo}.txt", "r").read()
                diff = diff.replace('\r', '')
                adiff = comment["hunk_diff"]
                adiff = adiff.replace('\r', '')

                # calculate intersection
                regex = re.compile(r'@@ \-(\d+),(\d+) \+(\d+),(\d+) @@')
                lines = regex.findall(adiff)
                if len(lines) <= 0:
                    logger.warning(f"{prid} {file_path} {comment_id} no match")
                    # print(adiff)
                    continue
                line = lines[0]
                cmtstart_line = int(line[2])
                cmtend_line = cmtstart_line + int(line[3]) - 1
                lines2 = regex.findall(diff)
                if len(lines2) <= 0:
                    continue
                patchnum = 0
                while patchnum < len(lines2):
                    line = lines2[patchnum]
                    cmmitstart_line = int(line[0])
                    cmmitend_line = cmmitstart_line + int(line[1]) - 1
                    if set(range(cmtstart_line, cmtend_line + 1)) & set(range(cmmitstart_line, cmmitend_line + 1)):
                        cmtgot = True
                        break
                    patchnum += 1
                if cmtgot:
                    break
            if not cmtgot:    # not aligned in this commit
                continue
            ret = os.system(f"filterdiff --hunks={patchnum+1} {tmppath}/diff-{lang}-{filerepo}.txt > {tmppath}/hunk-{lang}-{filerepo}.txt")
            if ret < 0:
                logger.warning(f"Extracting hunk failed.")
                continue
            with open(f"{tmppath}/hunk-{lang}-{filerepo}.txt") as f:
                for __ in range(4):      # drop 4 lines
                    f.readline()
                hunk = f.read()
            result = {"old_hunk": comment["hunk_diff"], "oldf": old_contents, "hunk": hunk, "comment": comment["message"], "ids": [comment["id"], commit["hash"], allcommits[nextidx]["hash"]]}
            result["repo"] = repo
            result["ghid"] = pr["gh_number"]
            data.append(result)
            # logger.warning(f"Succeeded.")
    # use hunk to deduplicate
    dedup_dict = {}
    for dic in data:
        key = dic["old_hunk"]
        if key not in dedup_dict:
            dedup_dict[key] = dic
    data = list(dedup_dict.values())    
    write_jsonl(data, f"{outpath}/review_ref_{lang}_{repo.replace('/', '-')}.jsonl")
    os.system(f"rm {tmppath}/a-{lang}-{filerepo}.txt {tmppath}/b-{lang}-{filerepo}.txt {tmppath}/diff-{lang}-{filerepo}.txt {tmppath}/hunk-{lang}-{filerepo}.txt")


main()