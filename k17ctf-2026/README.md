# k17ctf — 比赛记录

> 赛后整理：题目存档 + writeup + exploit。

| | |
|---|---|
| **赛事** | k17ctf（2026 年 9 月） |
| **队伍** | ByteVoid |
| **成绩** | 解出 **26 / 37** 题 |
| **存档** | 2026-09-11 抓取题面与附件 |

## 目录结构

```
k17ctf-2026/
├── README.md          # 本文件：赛事记录 + 题目索引
├── FLAGS.md           # 解出的 flag 清单（赛后公开）
├── challenges/<分类>/<slug>/
│   ├── README.md      # 平台题面 + 附件哈希
│   ├── WRITEUP.md     # 解题记录
│   ├── exploit.*      # 利用脚本
│   └── ...            # 附件原文
└── tools/scrape.py    # 抓取题面/附件的脚本
```

## 题目索引

| # | 题目 | 分类 | 难度 | 分值 | 解出 | writeup | flag |
|---|------|------|------|------|------|:---:|:---:|
| 9 | [blowfish](challenges/crypto/blowfish) | crypto | hard | 119 | 96 | 待补 | ✅ |
| 10 | [cry-pto](challenges/crypto/cry-pto) | crypto | beginner | 100 | 238 | ✅ | ✅ |
| 11 | [cryjail](challenges/crypto/cryjail) | crypto | hard | 147 | 69 | ✅ | ✅ |
| 12 | [leaky rsa](challenges/crypto/leaky-rsa) | crypto | easy | 100 | 234 | ✅ | ✅ |
| 13 | [shamir secret spilling](challenges/crypto/sss) | crypto | medium | 100 | 150 | ✅ | ✅ |
| 17 | [close enough](challenges/forensics/close-enough) | forensics | easy | 100 | 208 | ✅ | ✅ |
| 23 | [get fixed boi](challenges/forensics/get-fixed-boi) | forensics | medium | 114 | 102 | ✅ | ✅ |
| 14 | [discord](challenges/meta/discord) | meta | easy | 100 | 344 | — | — |
| 15 | [sanity check](challenges/meta/sanity-check) | meta | beginner | 100 | 389 | 待补 | ✅ |
| 16 | [archive trap](challenges/misc/archive-trap) | misc | easy | 100 | 169 | ✅ | ✅ |
| 18 | [P = NP](challenges/misc/p-np) | misc | beginner | 100 | 258 | ✅ | ✅ |
| 19 | [verify you are human](challenges/misc/verify-you-are-human) | misc | medium | 113 | 103 | ✅ | ✅ |
| 20 | [prime calc](challenges/misc/prime-calc) | misc | hard | 189 | 44 | — | — |
| 21 | [spot](challenges/misc/spot) | misc | hard | 201 | 39 | — | — |
| 22 | [sudo but good](challenges/misc/sudobutgood) | misc | medium | 136 | 78 | ✅ | ✅ |
| 24 | [larpfest](challenges/osint/larpfest) | osint | easy | 100 | 169 | ✅ | ✅ |
| 25 | [rainier](challenges/osint/rainier) | osint | beginner | 100 | 240 | 待补 | ✅ |
| 26 | [big-win](challenges/pwn/big-win) | pwn | easy | 100 | 146 | ✅ | ✅ |
| 27 | [huge binary 1](challenges/pwn/huge-binary-easy) | pwn | easy | 111 | 106 | ✅ | ✅ |
| 28 | [huge binary 2](challenges/pwn/huge-binary) | pwn | hard | 216 | 34 | — | — |
| 29 | [ihyh](challenges/pwn/ihyh) | pwn | hard | 207 | 37 | — | — |
| 30 | [java notes](challenges/pwn/java-notes) | pwn | medium | 143 | 72 | ✅ | ✅ |
| 31 | [make-a-wish](challenges/pwn/make-a-wish) | pwn | medium | 148 | 68 | ✅ | ✅ |
| 32 | [not json](challenges/pwn/notjson) | pwn | hard | 210 | 36 | — | — |
| 33 | [online-roulette](challenges/pwn/online-roulette) | pwn | beginner | 100 | 146 | ✅ | ✅ |
| 34 | [waf](challenges/pwn/waf) | pwn | medium | 181 | 48 | — | — |
| 35 | [etch-a-sketch](challenges/rev/etchasketch) | rev | easy | 100 | 192 | ✅ | ✅ |
| 36 | [Evilgram](challenges/rev/evilgram) | rev | medium | 100 | 147 | ✅ | ✅ |
| 37 | [monoid](challenges/rev/monoid) | rev | medium | 100 | 165 | ✅ | ✅ |
| 38 | [reverse captcha](challenges/rev/reverse-captcha) | rev | beginner | 100 | 255 | — | — |
| 39 | [srev](challenges/rev/srev) | rev | hard | 117 | 98 | 待补 | ✅ |
| 3 | [DriveOne](challenges/web/driveone) | web | hard | 141 | 74 | ✅ | ✅ |
| 4 | [Duplex](challenges/web/duplex) | web | hard | 132 | 82 | ✅ | ✅ |
| 5 | [edwalk](challenges/web/edwalk) | web | beginner | 100 | 259 | — | — |
| 6 | [macrohard azuer](challenges/web/macro-hard) | web | medium | 100 | 123 | — | — |
| 7 | [polynomial evaluator](challenges/web/polynomial-eval) | web | medium | 163 | 58 | ✅ | ✅ |
| 8 | [whatsNew](challenges/web/whatsnew) | web | hard | 194 | 42 | — | — |

## 说明

- 共 37 题，解出 26 题，其中 22 题留下了 writeup。
- 未解的 11 题同样保留了题面与附件，方便日后复盘。
- 题目与附件的版权归 k17ctf 出题人所有，此处仅作赛后备档与学习用途；
  所有实例地址与实例凭据均已移除。
