| Dataset | Train # | Valid # | Test # | LOC |
| :------ | :-----: | :-----: | :-----: | :-: |
| Diff Quality Estimation |  ~266k  |  ~31k  | ~31k  | ~11M  |
| Review Comment Generation | ~118k | ~10k | ~10k | ~1.8M |
| Code Refinement | ~150k | ~13k | ~13k | ~1.3M |



Msg:
117,739 + 10,xxx + 10,xxx
1,541,997 + 124,481 + 122,418

Ref:
150,406 + 13103 + 13103
1,065,611 + 92,121 + 92,746


| Lang | Projects | PRs | Data Size |  w/o comment | w comment |
| :--: | :------: | :--: | :---: | :---------: | :-----------: |
| Python | 195 | 1451 | 72.8G | 887 | 518 |
| Java  | 175 | 1073 | 54.8G | 876 | 467 |
| Go | 146 | 951 | 40.4G | 728 | 410 |
| C++ | 133 | 999 | 82.1G |  474 | 202 |
| JavaScript  | 194 | 1354 | 30.6G |  425 | 293 |
| C  | 77 | 441  | 135.4G | 292 | 110 |
| C#  | 77  | 463  | 28.2G | 324 | 199 |
| Php | 92 | 574 | 16.0G | 215 | 157 |
| Ruby | 72 | 626 | 3.8G | 90  | 126 |
| Total | 1161 | 7,933k | 463.2G | 4,311k | 2,481k |


32732   1480
138988  6070

Cls train: 265836.
Msg train: 132918.
Cls valid: 31252.
Cls test: 31252.
Msg valid: 15626.
Msg test: 15626.

Ref valid: 13103
Ref test: 13104