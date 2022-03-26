token=[gh_token]

repos=(
arangodb/arangodb,js
)


for repo in "${repos[@]}"
do
    arrIN=(${repo//,/ })
    repo=${arrIN[0]}
    lang=${arrIN[1]}
    ends=$lang
    python -u pull_file.py --db $repo --repo $repo --lang $lang \
            --tmppath tmpfspl --token $token --ends $ends >> logs/$lang-pf.txt
    python -u create_cls_dataset.py --db $repo --repo $repo --lang $lang \
            --tmppath tmpfscr --outpath reviews --token $token >> logs/$lang-cls.txt
#     python -u create_gen_dataset.py --db $repo --repo $repo --lang $lang \
#             --tmppath tmpfscr2 --outpath reviews --token $token >> logs/$lang-gen.txt
    python -u create_refine_dataset.py --db $repo --repo $repo --lang $lang \
            --tmppath tmpfsref --outpath refs --token $token --ends $ends >> logs/$lang-refn.txt
done
