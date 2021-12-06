import os, json
from tqdm import tqdm
import random
import re


def cleanmsg(msg):
    msg = msg.replace("\r\n", "\n")
    msg = re.sub(r"!?\[.*?\]\(.*?\)", " ", msg)
    msg = re.sub(r"( |\n)http(s?)://(.*?)( |\n)", " ", msg)
    return msg.encode("ascii", "ignore").decode("ascii")




path = "/home/v-zhuoli1/lzzz/reviews"
for lang in ["go", "javascript", "php", "python", "ruby"]:
    print(f"Start creating data for {lang}.")

    files = os.listdir(path)
    clsdata, gendata = [], []


    clsfiles = [file for file in files if file.startswith(f"review_cls_{lang}")]    
    for file in clsfiles:
        with open(os.path.join(path, file)) as f:
            data = json.load(f)
            for dic in data:
                dic["project"] = file
            clsdata += data
    ftclsdata = [dic for dic in clsdata if len(dic["patch"].split()) <= 500]
    print(f"Length of cls: {len(ftclsdata)}")
    with open(f"processed/{lang}_cls.jsonl", "w") as f:
        for dic in ftclsdata:
            f.write(json.dumps(dic) + "\n")


    genfiles = [file for file in files if file.startswith(f"review_gen_{lang}")]
    for file in genfiles:
        with open(os.path.join(path, file)) as f:
            data = json.load(f)
            for dic in data:
                dic["project"] = file
            gendata += data
    # print(len(gendata))
    ftgendata = [dic for dic in gendata if len(dic["patch"].split()) <= 500]
    for dic in ftgendata:
        dic["msg"] = cleanmsg(dic["msg"])
    ftgendata = [dic for dic in ftgendata if len(dic["msg"].split()) in range(2, 200)]
    print(f"Length of gen: {len(ftgendata)}")

    with open(f"processed/{lang}_gen.jsonl", "w") as f:
        for dic in ftgendata:
            f.write(json.dumps(dic) + "\n")