import os, sys, time
import logging
import pprint
import requests
from tqdm import tqdm
from utils import get_cursor, get_all, get_from_attr, findkth
pprint = pprint.PrettyPrinter(indent=4).pprint

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(stream=sys.stdout, format=FORMAT)
logger = logging.getLogger("filepuller")


def main():
    user, password = "FAREAST.v-zhuoli1", "passward"
    db = "etcr"
    repo = "elastic/elasticsearch"
    token = "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"
    conn, cur = get_cursor(db, user, password)
    comments = get_all(cur, "comment")
    filtered_cmts = [cmt for cmt in comments if cmt["hunk_file"] and cmt["hunk_file"].endswith(".java")]

    headers = {"Authorization": f"token {token}"}
    not_found = ['400: Invalid request', '404: Not Found']

    # CREATE table
    try:
        logger.warning("Creating table comment_file_pair.")
        cur.execute(f"create table comment_file_pair (id bigint primary key, file_path text, oldf text, newf text, diff text);")
        conn.commit()
    except Exception as e:
        logger.warning(str(e))
        conn, cur = get_cursor(db, user, password)
    succ = 0
    totallen = len(filtered_cmts)
    filtered_cmts = sorted(filtered_cmts, key=lambda v: v["id"])
    logger.warning(f"Start to crawl files for {totallen} comments.")
    # CRAWL Files
    for NUMBER, cmt in enumerate(filtered_cmts):
        logger.warning(f"{NUMBER}-th comment.")
        tryfbid = False
        file_path = cmt["hunk_file"]
        commit_id = cmt["commit_id"]
        commit_fb_id = cmt["commit_fallback_id"]
        if not commit_id:
            # logger.warning(f"\tEmpty commit_id for comment {cmt['id']}")
            if not commit_fb_id:
                logger.warning(f"\tEmpty commit_fallback_id for comment {cmt['id']}")
                continue
            else:
                tryfbid = True
                logger.warning(f"\tTry with commit_fallback_id")
                commit_id = commit_fb_id
        try:
            commit = get_from_attr(cur, "commit", "id", commit_id)[0]
        except:
            logger.warning(f"\tcommit_id not found in comment {cmt['id']}")
            continue
        # get current commit hash value
        hashv = commit["hash"]
        pullreqid = commit["pull_request_id"]
        # get all commits related to this request
        commits = get_from_attr(cur, "commit", "pull_request_id", pullreqid)
        commits = sorted(commits, key=lambda v: v["created_at"])
        try:
            assert len(commits) > 0
        except:
            logger.warning(f"\tNone commits in PR {pullreqid}")
            continue
        first_commit = commits[0]
        first_hashv_b = first_commit["hash_parent"]
        # diff between current commit and first_commit in this PR
        try:
            oldurl = f"https://raw.githubusercontent.com/{repo}/{first_hashv_b}/{file_path}"
            newurl = f"https://raw.githubusercontent.com/{repo}/{hashv}/{file_path}"
            old_contents = requests.get(oldurl, headers=headers).text
            new_contents = requests.get(newurl, headers=headers).text
            if old_contents in not_found:
                # logger.warning(f"\tEmpty file with oldurl {oldurl}")
                # continue
                old_contents = ""
            if new_contents in not_found:
                logger.warning(f"\tEmpty file with newurl {newurl}, passing comment {cmt['id']}")
                continue
        except:
            logger.warning(f"\tError during pull file {oldurl} ++ {newurl}")
            continue
        open("tmpa.txt", "w").write(old_contents)
        open("tmpb.txt", "w").write(new_contents)
        os.system("git diff --no-index tmpa.txt tmpb.txt > tmpdiff.txt")
        # diff = difflib.unified_diff(old_contents.splitlines(keepends=True), 
        #         new_contents.splitlines(keepends=True), fromfile=file_path.split("/")[-1], tofile=file_path.split("/")[-1])
        # diff = "".join(diff)
        diff = open("tmpdiff.txt", "r").read()
        diff = diff.replace('\r', '')
        adiff = cmt["hunk_diff"]
        adiff = adiff.replace('\r', '')
        newlineidx = adiff.find("\n")
        if newlineidx == -1:
            newlineidx = 0
        # only check first 10 lines
        truncidx = findkth(adiff, "\n", 10)     # if diff hunk less than 10 lines, it's ok to be -1
        bdiff = adiff[newlineidx:truncidx]
        if diff.find(bdiff) < 0:
            if not tryfbid:
                logger.warning(f"\tNot matched for comment {cmt['id']}")
            else:
                logger.warning(f"\tTry fallback_id fail.")
            continue
        logger.info(f"Insert value to table comment_file_pair.")
        data = {
            "id": cmt["id"],
            "file_path": file_path,
            "oldf": old_contents,
            "newf": new_contents,
            "diff": diff
        }
        try:
            cur.execute(f"insert into comment_file_pair\
                values (%(id)b, %(file_path)s, %(oldf)s, %(newf)s, %(diff)s);", data)
            logger.warning(f"\tCrawling files for {NUMBER}-th comment succeeded.")
        except Exception as e:
            logger.warning(str(e))
            conn, cur = get_cursor(db, user, password)
            continue
        # time.sleep(0.8)
        succ += 1
        if (NUMBER + 1) % 1000 == 0:
            conn.commit()
    conn.commit() 
    os.system("rm tmpa.txt tmpb.txt tmpdiff.txt")


main()