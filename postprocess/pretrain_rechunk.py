import os, json
import logging
import math

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


datadir = "/home/v-zhuoli1/lzzz/reviewdata.bc/final"
outputdir = "/home/v-zhuoli1/lzzz/pretrain_chunks"
if not os.path.exists(outputdir):
    os.makedirs(outputdir)
outpre = "chunk_"
infiles = [f for f in os.listdir(datadir) if f.startswith("pretrain") and f.endswith(".jsonl")]
logger.warning(f"Input files: {len(infiles)}")
logger.warning(f"Input file examples: {infiles[:3]}")
outidx = 0
outlist = []
magicnum = 9272964      # magic number got from previous statistics
breakcnt = math.ceil(magicnum / 66)
cnt = 0
for infile in infiles:
    with open(os.path.join(datadir, infile), "r") as f:
        for line in f:
            cnt += 1
            outlist.append(line.strip())
            if len(outlist) == breakcnt:
                outfile = outpre + str(outidx) + ".jsonl"
                with open(os.path.join(outputdir, outfile), "w") as f:
                    for item in outlist:
                        f.write(item + "\n")
                outidx += 1
                outlist = []
                logger.warning(f"{outidx} files written.")
if len(outlist) > 0:
    outfile = outpre + str(outidx) + ".jsonl"
    with open(os.path.join(outputdir, outfile), "w") as f:
        for item in outlist:
            f.write(item + "\n")
    outidx += 1
    logger.warning(f"{outidx} files written.")
logger.warning(f"{cnt} lines read.")