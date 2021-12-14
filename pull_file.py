import os, sys, time
import logging
import pprint
import requests
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
args = parser.parse_args()


def main():
    user, password = "FAREAST.v-zhuoli1", "passward"
    db, repo, lang, token = args.db, args.repo, args.lang, args.token
    ends = args.ends
    tmppath = args.tmppath
    filerepo = repo.replace("/", '-')
    conn, cur = get_cursor(db, user, password)
    comments = get_all(cur, "comment")
    filtered_cmts = [cmt for cmt in comments if cmt["hunk_file"] and cmt["hunk_file"].endswith(ends)]

    if not os.path.exists(f"{tmppath}"):
        os.mkdir(f"{tmppath}")

    headers = {"Authorization": f"token {token}"}
    not_found = ['400: Invalid request', '404: Not Found']

    # CREATE table
    try:
        logger.warning("Creating table comment_file_pair.")
        cur.execute(f"create table comment_file_pair (id bigint primary key, file_path text, oldf text, newf text, diff text);")
        conn.commit()
    except Exception as e:
        logger.warning(str(e))
        conn.close()
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
        allcommits = get_from_attr(cur, "commit", "pull_request_id", pullreqid)
        allcommits = sorted(allcommits, key=lambda v: v["created_at"])
        try:
            assert len(allcommits) > 0
        except:
            logger.warning(f"\tNone commits in PR {pullreqid}")
            continue
        comment_time = cmt['created_at']
        # get the index of the commit that is closest to the comment
        commentcommitid = cmt["commit_id"]
        if not commentcommitid:
            commitidx = 0
            while commitidx + 1 < len(allcommits) and allcommits[commitidx + 1]["created_at"] < comment_time:
                commitidx += 1
            commit = allcommits[commitidx]
        else:       # if there is commit id in comment, use it; do not have to use timeline
            try:
                commit = get_from_attr(cur, "commit", "id", commentcommitid)[0]
            except:
                logger.warning(f"\tcommit_id not found in comment {cmt['id']}")
                continue
        commit_id = commit["id"]
        # get current commit hash value
        hashv = commit["hash"]
        first_commit = allcommits[0]
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
        open(f"{tmppath}/a-{lang}-{filerepo}.txt", "w").write(old_contents)
        open(f"{tmppath}/b-{lang}-{filerepo}.txt", "w").write(new_contents)
        os.system(f"git diff --no-index {tmppath}/a-{lang}-{filerepo}.txt {tmppath}/b-{lang}-{filerepo}.txt > {tmppath}/diff-{lang}-{filerepo}.txt")
        diff = open(f"{tmppath}/diff-{lang}-{filerepo}.txt", "r").read()
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
            "diff": diff,
            "repo": repo
        }
        try:
            cur.execute(f"insert into comment_file_pair (id, file_path, oldf, newf, diff)\
                values (%(id)b, %(file_path)s, %(oldf)s, %(newf)s, %(diff)s) \
                on conflict (id) do update set file_path = excluded.file_path, \
                oldf = excluded.oldf, newf = excluded.newf, diff = excluded.diff;", data)
            logger.warning(f"\tCrawling files for {NUMBER}-th comment succeeded.")
        except Exception as e:
            logger.warning(str(e))
            conn.close()
            conn, cur = get_cursor(db, user, password)
            continue
        # time.sleep(0.8)
        succ += 1
        if (NUMBER + 1) % 1000 == 0:
            conn.commit()
    conn.commit() 
    os.system(f"rm {tmppath}/a-{lang}-{filerepo}.txt {tmppath}/b-{lang}-{filerepo}.txt {tmppath}/diff-{lang}-{filerepo}.txt")


main()