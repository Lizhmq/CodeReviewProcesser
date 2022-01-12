import psycopg
import json


def write_jsonl(jss, filename):
    with open(filename, "w") as f:
        for js in jss:
            f.write(json.dumps(js) + "\n")


def get_cursor(db, user, password):
    conn = psycopg.connect(f"dbname={db} user={user} password={password}")
    cur = conn.cursor()
    return conn, cur

def get_all(cur, table):
    assert table in ("pull_request", "commit", "comment", "git_file", "ast")
    cur.execute(f"SELECT * from {table}")
    out = cur.fetchall()
    key = [col.name for col in cur.description]
    ret = []
    for item in out:
        dic = dict()
        for k, v in zip(key, item):
            dic[k] = v
        ret.append(dic)
    return ret


def get_all_attr(cur, table, attr):
    assert table in ("pull_request", "commit", "comment", "git_file", "ast")
    cur.execute(f"SELECT {attr} from {table}")
    out = cur.fetchall()
    return out

def get_from_id(cur, table, id):
    assert table in ("pull_request", "commit", "comment", "git_file", "ast")
    cur.execute(f"SELECT * from {table} where id = {id}")
    out = cur.fetchone()
    key = [col.name for col in cur.description]
    dic = dict()
    for k, v in zip(key, out):
        dic[k] = v
    return dic

def get_attr_from_id(cur, table, attr, id):
    assert table in ("pull_request", "commit", "comment", "git_file", "ast")
    cur.execute(f"SELECT {attr} from {table} where id = {id}")
    out = cur.fetchone()
    return out[0]

def get_from_attr(cur, table, attr, attrid):
    assert table in ("pull_request", "commit", "comment", "git_file", "ast")
    cur.execute(f"SELECT * from {table} where {attr} = {attrid}")
    out = cur.fetchall()
    key = [col.name for col in cur.description]
    ret = []
    for item in out:
        dic = dict()
        for k, v in zip(key, item):
            dic[k] = v
        ret.append(dic)
    return ret

def gen_dic(description, data):
    key = [col.name for col in description]
    ret = []
    for item in data:
        dic = dict()
        for k, v in zip(key, item):
            dic[k] = v
        ret.append(dic)
    return ret
    
def clean_1stline_diff(s):
    idx2 = s.find("\n")        # remove strange thing in "@@ -, + @@" line
    idx1 = s.find("@@", 2)
    bdiff = s[:idx1+2] + s[idx2:]
    return bdiff

def findkth(s, subs, k):
    ret = 0
    while k > 0:
        ret = s.find(subs, ret)
        if ret == -1:
            return -1
        ret = ret + len(subs)
        k -= 1
    return ret