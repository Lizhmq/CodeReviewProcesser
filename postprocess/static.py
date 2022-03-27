import os
import json


def str2repo(s):
    s = s.split("/")[-1]    # get filename
    tmplist = s.split("_")
    tmplist[-1] = tmplist[-1][:-6]
    type = tmplist[1]
    lang = tmplist[2]
    repo = "_".join(tmplist[3:])
    return {"repo": repo, "lang": lang, "type": type}

def getprdic():
    path = "/home/v-zhuoli1/lzzz/TopRepos/repos"
    langs = ["javascript", "python", "java", "php", "c-plus-plus", "ruby", "c-sharp", "go", "c"]
    returndic = {}
    for lang in langs:
        langp = os.path.join(path, f"{lang}_withpr.json")
        with open(langp, "r") as f:
            data = json.load(f)
        for a, b in data:
            a = a.replace("/", "-")
            returndic[a] = int(b)
    return returndic

langrepo = {}
langclscnt = {}
langgencnt = {}
prdic = getprdic()
langprdic = {}

def main():
    outputdir = "/home/v-zhuoli1/lzzz/reviewdata.bc/final"
    file1 = "statistics.json"
    file2 = "statistics2.json"
    for file in [file1, file2]:
        with open(outputdir + "/" + file, "r") as f:
            data = json.load(f)
        for repostr, cnt in data:
            dic = str2repo(repostr)
            lang, repo, type = dic["lang"], dic["repo"], dic["type"]
            if lang[0] == ".":
                lang = lang[1:]
            if lang not in langrepo:
                langrepo[lang] = set()
            langrepo[lang].add(repo)
            if lang not in langclscnt:
                langclscnt[lang] = 0
            if lang not in langgencnt:
                langgencnt[lang] = 0
            if type == "cls":
                langclscnt[lang] += cnt
            else:
                langgencnt[lang] += cnt
    # print("langrepo:", langrepo)
    for key, value in langrepo.items():
        langprdic[key] = sum(prdic[repo] for repo in value)
    print(sum(map(len, langrepo.values())))
    print(sum([prdic[repo] for repos in langrepo.values() for repo in repos]))
    newclscnt = {}
    for key in langclscnt:
        newclscnt[key] = langclscnt[key] - langgencnt[key]
    print("langclscnt:", newclscnt)
    print("langgencnt:", langgencnt)
    print(sum(newclscnt.values()))
    print(sum(langgencnt.values()))
    for key in langprdic:
        print(key, len(langrepo[key]), round(langprdic[key] / 1000),\
                                         round(newclscnt[key] / 1000), round(langgencnt[key] / 1000))
    print(sum(len(langrepo[key]) for key in langrepo))
    print(sum(langprdic[key] for key in langprdic) / 1000)
    print(sum(newclscnt[key] for key in newclscnt) / 1000)
    print(sum(langgencnt[key] for key in langgencnt) / 1000)
main()
