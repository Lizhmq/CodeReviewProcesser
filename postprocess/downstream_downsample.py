import os
import json, random

def ds_data(inpath, outpath):

    msg, cls = 0, 0
    out = []
    with open(inpath, encoding="utf-8") as f:
        for line in f:
            dic = json.loads(line)
            # if len(dic["patch"].split("\n")) > 20:           # to fileter long data
            #     continue                                     # uncomment these when you process msg data
            if dic["y"] == 1 and dic["msg"] != "":
                msg += 1
                out.append(line.strip() + "\n")
            elif dic["y"] == 0 and dic["msg"] == "":
                cls += 1

    balance_ratio = msg / cls
    print(msg, cls, balance_ratio)
    with open(inpath, encoding="utf-8") as f:
        for line in f:
            dic = json.loads(line)
            # if len(dic["patch"].split("\n")) > 20:            # uncomment these when you process msg data
            #     continue
            if dic["y"] == 0 and dic["msg"] == "":
                if random.random() < balance_ratio + 0.1:   # add 0.1 to get more no msg data
                    out.append(line.strip() + "\n")
    with open(outpath, "w", encoding="utf-8") as f:
        for line in out:
            f.write(line)


path = "newdata"
files = os.listdir(path)
files = [os.path.join(path, file) for file in files if file.startswith("outrain-lang")]
for file in files:
    ds_data(file, file.replace("outrain", "outtraintmp"))
    print(f"{file} done")