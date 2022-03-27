import json
import argparse


def main():
    parser = argparse.ArgumentParser(description='Remove stopwords from a JSON file.')
    parser.add_argument('-i', '--input', help='Input JSON file', required=True)
    parser.add_argument('-o', '--output', help='Output JSON file', required=True)
    args = parser.parse_args()

    stopwords = open("stopwords.txt").readlines()
    stopwords = [stopword.strip() for stopword in stopwords]

    data = []
    with open(args.input, 'r') as f:
        for line in f:
            dic = json.loads(line)
            comment = dic["msg"]
            # print(comment)
            comment = " ".join([word for word in comment.split() if word.lower() not in stopwords])
            dic["msg"] = comment
            # print(comment)
            data.append(dic)
    with open(args.output, 'w') as f:
        for dic in data:
            f.write(json.dumps(dic) + "\n")

if __name__ == "__main__":
    main()