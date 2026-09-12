# etch-a-sketch — Writeup

**Flag**: `K17{my_masterpiece}`
**Category**: rev · easy · 100 pts
**Attachment**: `etchasketch` (ELF x86-64 PIE, not stripped, sha256 `2daeed4c…64b5`)

## TL;DR

程序把 `.rodata` 里的一张"线段表"用**半径 10 的方形画笔**画到 120×82 的画布上再打印。
笔太粗，正常输出的 91% 像素都是 `#`，图完全糊掉。把 `brush_r` 改成 0 再跑（或直接按线段表细线重绘），
就得到：

```
K17{my_masterpiece}
```

```sh
# 一行解：笔刷半径 10 -> 0，然后跑
python3 -c "d=bytearray(open('etchasketch','rb').read()); d[0x3020]=0; open('p','wb').write(d)"
qemu-x86_64-static -L /usr/x86_64-linux-gnu ./p        # aarch64 上跑 x86-64 用 qemu + 交叉 sysroot
```

## 题面

> I drew you a picture, hope you like it <3

只有一个 16 KB 的 x86-64 ELF，纯计算 + `putchar`，无输入、无网络。

## 逆向

符号没剥，函数只有三个：`main` @ `0x12df`、`line` @ `0x11e5`、`dab` @ `0x1149`。

### 数据结构

| 符号 | 地址 | 说明 |
|------|------|------|
| `points` | `.rodata` `0x2020` | `int32_t[325]`，325 个点（1300 字节，正好铺满 rodata 尾部） |
| `brush_r` | `.data` `0x4020` | 画笔半径，**值 = 10** |
| `canvas` | `.bss` `0x4060` | `uint8_t[120*82]`，0 = 空，非 0 = 画过 |

`points` 每个元素是打包坐标 **`(y << 16) | x`**（低 16 位 = x/列，高 16 位 = y/行）。
`-1`（即 `0xffffffff`，低 16 位为负）表示**抬笔**，`0xfffe` 是终止符。

### `main` 的逻辑

```c
for (i = 0; i <= 324; i++) {
    if ((points[i] & 0xffff) == 0xfffe) break;      // 终止
    if (!(points[i] & 0x8000) && !(prev & 0x8000))  // 当前点和上一点都非"抬笔"
        line(prev, points[i]);                      // 画一条线段
    prev = points[i];
}
// 打印：canvas 非 0 -> '#'，否则 ' '
for (y = 0; y <= 0x51; y++) {           // 82 行
    for (x = 0; x <= 0x77; x++)         // 每行 120 字符
        putchar(canvas[y*120 + x] ? '#' : ' ');
    putchar('\n');
}
```

### `dab` / `line`

`line` 是标准 Bresenham，但把两个点当作 32 位打包值：低 16 位取 x、高 16 位取 y，
在每一步调用 `dab(x, y)`。`dab` 画一个**边长为 `2*brush_r+1` 的实心方块**：

```c
r = brush_r;                                  // = 10
for (dy = -r; dy <= r; dy++)
    for (dx = -r; dx <= r; dx++)
        if (0 <= x+dx <= 119 && 0 <= y+dy <= 81)
            canvas[(y+dy)*120 + (x+dx)] = 1;
```

所以每个落笔点其实糊上 21×21 = 441 个像素。

## 卡点：笔太粗，图被涂满

直接跑（或用 Python 逐条仿真）得到的输出是 82 行 × 120 列，**91.2% 是 `#`**：

```
#########################################################################               
########################################################################################
...
```

整张画布基本全黑，只剩右侧一块空白，"画"了什么完全看不出来 —— 这就是上一轮
在渲染方向/翻转/转置上反复试却没结果的原因：**不是方向错了，是笔刷半径把信息盖掉了**。

## 还原

线段表是**原样存在二进制里**的（`points` 在 `.rodata`），画笔只是"渲染参数"，
所以有两条等价的路：

### 方法 A（推荐，最直接）：把 `brush_r` 改成 0

`brush_r` 在文件偏移 **`0x3020`**（vaddr `0x4020` − (.data 段 vaddr `0x4010` − 文件偏移 `0x3010`)），
原值 `0x0a`：

```
$ readelf -x .data etchasketch
  0x00004020 0a000000                             ....
```

把这一字节改成 `00` 再跑，`dab` 退化成只画中心点，输出就是细线图。

### 方法 B：不改二进制，自己按线段表细线重绘

```python
import struct
d = open('etchasketch','rb').read()
pts = struct.unpack_from('<325i', d, 0x2020)
s16 = lambda v: v - 0x10000 if v & 0x8000 else v
W, H = 120, 82
c = [[0]*W for _ in range(H)]

def dline(p1, p2):                       # 与 line() 等价的 Bresenham
    x1, y1 = p1; x2, y2 = p2
    dx, dy = abs(x2-x1), -abs(y2-y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err, cx, cy = dx+dy, x1, y1
    c[cy][cx] = 1
    while (cx, cy) != (x2, y2):
        e2 = 2*err
        if e2 >= dy: err += dy; cx += sx
        if e2 <= dx: err += dx; cy += sy
        c[cy][cx] = 1

prev = -1
for v in pts:
    if (v & 0xffff) == 0xfffe: break
    if not (v & 0x8000) and not (prev & 0x8000):
        dline((s16(prev & 0xffff), s16((prev >> 16) & 0xffff)),
              (s16(v & 0xffff),    s16((v >> 16) & 0xffff)))
    prev = v
```

线段表共 **108 条线段**（每条 2 个点，`-1` 分隔），x ∈ [4,112]、y ∈ [3,75]。

## 实测

本机是 aarch64，用 `qemu-x86_64-static` + 系统里的交叉 sysroot `/usr/x86_64-linux-gnu` 跑的原程序：

```
$ qemu-x86_64-static -L /usr/x86_64-linux-gnu ./etchasketch | wc -c
9922                                  # 82*(120+1)，与 python 仿真逐字节一致
$ python3 -c "d=bytearray(open('etchasketch','rb').read()); d[0x3020]=0; open('p','wb').write(d)"
$ qemu-x86_64-static -L /usr/x86_64-linux-gnu ./p     # 细线版
```

细线版输出的前几行（`#` = 画过的像素）：

```
    #           #         #         #############         #####
    #         ##         ##                    #         #
    #        #          # #                    #        #
    #      ##          #  #                   #         #
    #     #           #   #                   #         #
    #   ##                #                  #          #
    #  #                  #                  #         ##
    ###                   #                 #       ##              # ###   ###     #           #
    ###                   #                #         ##             ##   # #   #     #         #
    #  #                  #                #           ##           #     #     #     #       #
    #   ##                #               #             #           #     #     #     #       #
    #     #               #               #             #           #     #     #      #     #
    #      ##             #              #              #           #     #     #       #   #
    #        #            #              #              #           #     #     #        # #
    #         ##          #             #                #          #     #     #        # #
    #           #   #############       #                 #####     #     #     #         #
```

三行文字分别是 `K17{my_` / `master` / `piece}`。**注意拼法是直接首尾相接**：
第一行末尾那个下划线就是分隔符，后两行之间没有下划线，所以是 `my_masterpiece` 而不是 `my_master_piece`。
（数一遍 `~/work/etch/patched_out.txt` 的字符网格可以确认：整个画布里只有**一个**下划线字形，在第 1 行 `my` 之后、基线下方第 4 行；第 2 行 `master` 之后到第 3 行 `piece` 之间没有任何下划线。）

```
K17{my_masterpiece}
```

## 备注 / 其他做法

- 也可以直接在 IDA/Ghidra 里看 `points`，或对 `brush_r` 下断点改寄存器；
  本质都是"原始的矢量数据在，只是渲染参数（笔宽）坑人"。
- 干扰点：`main` 里 `prev` 初值是 `-1`，且抬笔点自己也会更新 `prev`，
  所以点表中每个 `-1` 之后紧跟的那个点**不会**画线（因为 `prev & 0x8000` 为真），
  即 `-1` 是"抬笔 + 移动到新位置"，实现时别漏掉这个判断，否则会多出很多跨图的长线。
