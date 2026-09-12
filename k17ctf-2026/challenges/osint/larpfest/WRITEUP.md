# larpfest — WRITEUP

**Flag: `K17{l00k_im_a_1337_h4x0r}`**

## 题面

某人的 larp 拉满、OPSEC 为零。flag "在（或曾经在）" 这个仓库里：
`https://github.com/larp-larp-larp/larp`

## 解法

`git clone` 下来只有 3 个 commit，工作区里是几个无关紧要的文件（`code.cpp` 假 C++、
`wishlist.txt`、`my_os.png`、`.env` 里写着 `OPENAI_API_KEY="please ignore"`）。

关键在题面那句 **"or was"** —— 历史里删掉的东西还能捞：

```
$ git fsck --lost-found
dangling commit 2ff1293a0da908202dc16628e5c1fa68c05294ec

$ git cat-file -p 2ff1293a
tree b0962471...
parent 795d5d21...
chat said i needed this file          <- commit message
```

这个悬挂 commit（不是任何分支/ref 可达的，但 clone 时被一起打包下来了）的 tree 里有一个
43 字节的 blob：

```
$ git cat-file --batch-all-objects --batch-check | sort -k3 -n   # 找没被引用的 blob
85a039c7... blob 43
$ git cat-file -p 85a039c7
OPENAI_API_KEY="K17{l00k_im_a_1337_h4x0r}"
```

（真 key 被 force-push/rebase 从历史里"删"了，但对象还躺在 `.git/objects` 里。）

## 复现

```bash
git clone https://github.com/larp-larp-larp/larp && cd larp
git fsck --lost-found                      # 看 dangling commit
git cat-file -p <dangling-commit>          # 看 tree
git cat-file --batch-all-objects --batch-check   # 找孤儿 blob
git cat-file -p <blob>                     # flag
```

工作目录：`（本地上轮 session clone 的 repo）/`（上一轮 session clone 的）。

> 顺带：`my_os.png` 是干扰项，上一轮 session 在里面翻过通道/LSB（`~/larp/{chR,chG,chB,hidden,diff_*}.png`），没东西。
