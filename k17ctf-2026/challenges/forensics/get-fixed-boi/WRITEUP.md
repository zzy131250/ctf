# get fixed boi — WRITEUP

**Flag: `K17{cr1ms0n_0r_corrup73d}`**

## 题面

朋友发来一个 Terraria 世界存档，打不开（"I think he's cheating"）。修复它，并找出里面藏着的东西。
题目说明不需要有游戏本体也能做。

## 存档格式

`.wld`（version 319）结构：

```
[version:int32][magic:"relogic"][filetype:byte][revision:int32][favorite:u64]
[numSections:u16][(offset:int32,size:int32) * numSections]
...各 section 的 payload...
```

其中 tile 数据段从 `11946` 开始，按列 RLE 编码（`f1..f4` 旗标位决定后面跟哪些字段）。
世界 header 段里能看到 `crimson`（该世界的邪恶生物群系）。

**"打不开"的原因**：`chests` 段（起点 2753819）到 `signs` 段（起点 2772875）之间的
数据被破坏了。手写 parser 把 chests 段按 `int16 count / int16 max / 每箱 (x,y,name,item[max])`
解析，结束时偏移正好落在 `2772875`，一个字节不差 —— 说明只要按这个布局重写这段就能修好，
产出 `fixed_v319.wld`。世界能"打开"之后就能正常渲染了。

## 找到隐藏信息

把 4200×1200 的 tile 数组解出来（`tiles2.py` → `blocks2.npy`）后，在
**方块 ID 122（Ebonstone Brick）** 上做掩码，y ∈ [120,670] 这一段立刻显出**一整行由方块拼成的像素字体**：

```
cr1ms0n_0r_corrup73d
```

逐字核对（这一步很重要，方块字体里 `1/i`、`0/o`、`7/t` 极易混）：

| 位置 | 判据 |
|---|---|
| `cr1ms0n` | 第 3 字带左上小旗 + 底部衬线 → `1`；第 6 字是**带斜杠的圈** → `0`（同图里 `corr**o**p` 的 `o` 是不带斜杠的闭合圈，两者字形不同） |
| `0r` | 中间那个也是**带斜杠的圈**，所以是 `0r` 不是 `or` |
| `corrup73d` | 结尾 `7`（顶横 + 斜杠）`3`（双弧）`d`；`p` 有下伸部，`t` 不会有这种字形 |

另外 `signs` / `npc` 段都是 0 条，箱子里的物品名字全为空，所以藏东西的地方就是这行方块字。

flag = `K17{cr1ms0n_0r_corrup73d}`（读作 "crimson or corrupted"：这世界的邪恶群系是 crimson，
而存档本身是 corrupted，双关）。

## 复现

- 解析/修复：`scan.py`（定位 chests 段）、`ch2.py`/`ch3.py`/`chv.py`（试各种布局）、`tiles2.py`（解 tile 数组）
- 渲染文字：掩码 `blocks2.npy == 122`，裁 y∈[120,670] 逐字切开看（`word1_zoom.png` / `mid_zoom.png` / `w_or.png` / `w_corrupt.png`）
