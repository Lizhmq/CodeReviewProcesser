import os, json
from cleaner import DiffCleaner
from collections import Counter
from tqdm import tqdm


def test():
    diffC = DiffCleaner()
    testcmt = "```code here```, change to this please"
    cmt = diffC.cleanComment(testcmt)
    print(cmt)

def read_jsonl(path):
    data = []
    with open(path, "r") as f:
        for line in f:
            data.append(json.loads(line))
    return data

def write_jsonl(path, data):
    with open(path, "w") as f:
        for dic in data:
            f.write(json.dumps(dic) + "\n")

def cleanProj(data):
    dupcomments = set([p[0] for p in Counter(dic["comment"] for dic in data).items() if p[1] > 1])
    duphunks = set([p[0] for p in Counter(dic["hunk"] for dic in data).items() if p[1] > 1])
    filtdata = [dic for dic in data if dic["comment"] not in dupcomments and dic["hunk"] not in duphunks]
    ffdata = [dic for dic in filtdata if len(dic["hunk"].split("\n")) <= 20]
    return ffdata

def cleanData(data, diffC):
    ret = []
    for dic in data:
        dic["comment"] = diffC.cleanComment(dic["comment"])
        olds, news = diffC.cleanDiff(dic["hunk"])
        if dic["comment"][0] == "<" and dic["comment"][-1] == ">":
            # print(dic["comment"])
            continue
        if len(olds) == 0 or olds[0] == "<" and olds[-1] == ">":
            # print(olds)
            continue
        dic["old"] = olds
        dic["new"] = news
        ret.append(dic)
    return ret



if __name__ == "__main__":
    diffC = DiffCleaner()

    test_path = "/home/v-zhuoli1/wspace/CodeReviewProcesser/testrefs"
    files = os.listdir(test_path)
    files = [os.path.join(test_path, f) for f in files]
    full_data = []
    for file in tqdm(files):
        lang = file.split("_")[2]
        # print(lang)
        data = read_jsonl(file)
        data = cleanProj(data)
        data = cleanData(data, diffC)
        for i in range(len(data)):
            data[i]["lang"] = lang
        full_data += data
    print(f"Valid/test refine data length: {len(full_data)}")
    write_jsonl("./data/ref-validtest.jsonl", full_data)

    train_path = "/home/v-zhuoli1/wspace/CodeReviewProcesser/refs"
    files = os.listdir(train_path)
    files = [os.path.join(train_path, f) for f in files]
    with open("./data/ref-train-repos.json", "w") as f:
        f.write(str(files))
    split_l = 50000
    idx = 0
    full_data = []
    for file in tqdm(files):
        lang = file.split("_")[2]
        data = read_jsonl(file)
        data = cleanProj(data)
        data = cleanData(data, diffC)
        for i in range(len(data)):
            data[i]["lang"] = lang
        full_data += data
        if len(full_data) >= split_l:
            write_jsonl("./data/ref-train-{}.jsonl".format(idx), full_data)
            idx += 1
            full_data = []
    write_jsonl("./data/ref-train-{}.jsonl".format(idx), full_data)
    idx += 1
    print(f"{idx} files written.")
