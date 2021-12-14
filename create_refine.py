import os, sys, time
import re
import logging
import pprint
import requests
import json
import argparse
from tqdm import tqdm
from utils import get_cursor, get_all, get_from_attr, findkth
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


def main():
    user, password = "FAREAST.v-zhuoli1", "passward"
    db, repo, lang, token = args.db, args.repo, args.lang, args.token
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
    for pr in tqdm(FULLPRS):
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
            author = comment["author"]
            allcommits = [commit for commit in allcommits if commit["author"] != author]
            # comment and commit author are different
            if len(allcommits) == 0:
                continue
            if commit_id:
                firstidx = 0
                while firstidx < len(allcommits) and allcommits[firstidx]["id"] != commit_id:
                    firstidx += 1
                if firstidx < len(allcommits):
                    commit = allcommits[firstidx]
                else:
                    logger.warning(f"{prid} {file_path} {comment_id} not found")
            else:
                # get the index of the commit that is closest to the comment
                firstidx = 0
                while firstidx + 1 < len(allcommits) and allcommits[firstidx + 1]["created_at"] < comment_time:
                    firstidx += 1
                commit = allcommits[firstidx]
            hashv = commit["hash"]
            old_contents = "LINKO STARTO"
            cmtgot = False
            for nextidx in range(firstidx + 1, len(allcommits)):
                nexthashv = allcommits[nextidx]["hash"]
                try:
                    if old_contents == "LINKO STARTO":
                        oldurl = f"https://raw.githubusercontent.com/{repo}/{hashv}/{file_path}"
                        old_contents = requests.get(oldurl, headers=headers).text
                    newurl = f"https://raw.githubusercontent.com/{repo}/{nexthashv}/{file_path}"
                    new_contents = requests.get(newurl, headers=headers).text
                    if old_contents in not_found or new_contents in not_found:
                        if old_contents in not_found:
                            logger.warning(f"{oldurl} not found", end=" ")
                        if new_contents in not_found:
                            logger.warning(f"{newurl} not found")
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
                # logger.warning(diff)
                # logger.warning(adiff)
                # break
                lines2 = regex.findall(diff)
                if len(lines2) <= 0:
                    # logger.warning(f"Empty diff.")
                    continue
                patchnum = 0
                while patchnum < len(lines2):
                    line = lines2[patchnum]
                    cmmitstart_line = int(line[0])
                    cmmitend_line = cmmitstart_line + int(line[1]) - 1
                    # logger.warning(set(range(cmtstart_line, cmtend_line + 1)))
                    # logger.warning(set(range(cmmitstart_line, cmmitend_line + 1)))
                    if set(range(cmtstart_line, cmtend_line + 1)) & set(range(cmmitstart_line, cmmitend_line + 1)):
                        cmtgot = True
                        break
                    patchnum += 1
                if cmtgot:
                    break
            if not cmtgot:    # not aligned in this commit
                logger.warning(f"{prid} {file_path} {comment_id} not found")
                continue
            ret = os.system(f"filterdiff --hunks={patchnum+1} {tmppath}/diff-{lang}-{filerepo}.txt > {tmppath}/hunk-{lang}-{filerepo}.txt")
            if ret < 0:
                logger.warning(f"Extracting hunk failed.")
                continue
            with open(f"{tmppath}/hunk-{lang}-{filerepo}.txt") as f:
                for __ in range(4):      # drop 4 lines
                    f.readline()
                hunk = f.read()
            result = {"oldf": old_contents, "hunk": hunk, "comment": comment["message"], "ids": [comment["id"], commit["hash"], allcommits[nextidx]["hash"]]}
            result["repo"] = repo
            result["ghid"] = pr["gh_number"]
            data.append(result)
            logger.warning(f"Succeeded.")

# multiple comments?


    with open(f"{outpath}/testo_{lang}_{repo.replace('/', '-')}.json", "w") as f:
        json.dump(data, f)


    os.system(f"rm {tmppath}/a-{lang}-{filerepo}.txt {tmppath}/b-{lang}-{filerepo}.txt {tmppath}/diff-{lang}-{filerepo}.txt {tmppath}/hunk-{lang}-{filerepo}.txt")


main()