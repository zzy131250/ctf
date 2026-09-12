# big-win — Writeup

**Flag**: `K17{maybe_the_true_reward_is_the_stacks_we_pwned_along_the_way}`
**Category**: pwn · easy · 100 pts
**Target**: `nc chal.secso.cc 4001`

## TL;DR

`accum == 67` 让 `i` 自增两次，`i` 于是跳过 7，`while (i != SLOTS)` 永不结束 —— 得到无界 OOB 写。
而 `numbers[10]` 恰好压在局部变量 `i` 自己身上，把它改成 `-2`，`i++` 后正好落在 `-1`，
即 `numbers[-1] == noob.win`。把 `win` 覆盖成非 `0x67`，代码自己就会调用 `win()`。

**不需要 leak，不需要 ROP，不需要知道 win() 的地址。**

```
0 0 0 0 0 0 67 1 0 -2 0 0 0 0 0 0 0 0
```

## 漏洞

```c
while (i != SLOTS) {
    scanf("%d", &noob.numbers[i]);
    accum += noob.numbers[i];

    if (accum == 67) {          // <-- 这里 i++
        puts("thats a naughty naughty number, one less chance to win");
        i++;
    }
    SNAPSHOT();
    i++;
}
```

`i` 严格递增，唯一退出条件是 `i == 7`。一旦某次 `accum == 67` 把 `i` 从 6 推到 8，
循环就再也回不到 7 —— 于是 `numbers[i]` 一路往上写。

## 栈布局

远程 `SNAPSHOT`（`int3` + ptrace）会打印 `rbp-48` 到 `rbp+00` 的窗口。喂 `1 2 3 4 5 6 7`
并观察哪些字变化，即可反推布局：

| 表达式 | 地址 | 内容 |
|--------|------|------|
| `numbers[-1]` | `rbp-48` | **`noob.win`** |
| `numbers[0..6]` | `rbp-44 .. rbp-20` | 数组本体（合法范围） |
| `numbers[7..8]` | `rbp-16 .. rbp-12` | 未初始化填充 |
| `numbers[9]` | `rbp-8` | **`accum`** |
| `numbers[10]` | `rbp-4` | **`i` 自身** |
| `numbers[13..14]` | `rbp+8` | 返回地址 |

`rbp-8` 那个字是 `accum | (i << 32)`，从快照里能同时读出两个变量 —— 这是整个利用的反馈来源。

## 利用步骤

一次连接内：

1. **`i=0..5`** 全发 `0`，`i=6` 发 `67`。
   `accum` 恰好等于 67 → 触发 `i++` → `i=8`，**跳过 7，循环不再有条件退出**。
2. **`i=8`** 发 `1`（`accum` 67→68，避免再次 skip）。落在 `rbp-12` 填充区，无害。
3. **`i=9`** 发 `0`。这一次写入的目标是 `accum` 槽本身，于是 `accum = 0 + 0 = 0`。
4. **`i=10`** 发 `-2`。写入目标是 `i` 槽 → `i = -2`，`scanf` 返回后 `i++` → **`i = -1`**。
5. **`i=-1`** 发 `0` → `numbers[-1] = noob.win = 0`。
6. **`i=0..6`** 发 `0`，`accum` 保持 0，不再触发 skip → `i` 走到 7，循环退出。

此时 `noob.win == 0 != 0x67`，于是：

```c
puts("wtf you win???");
win();          // fopen("/flag","r") -> printf
```

## 为什么选 `i = -2` 而不是 `i = -7`

第一版我令 `i = -7`，想从 `-6` 一路走回 `-1`。`i=-6`（写 `rbp-68`）没问题，
但 `i=-5`（写 `rbp-64`）直接把进程打崩了 —— 那些地址已经在 `rbp-48` 帧外，
是 `printf`/`scanf` 自己的栈帧区，写进去会破坏调用链。

改成 `i = -2` 后，**所有写入都落在 `[rbp-48, rbp-4]` 帧内**，只读不写帧外（`accum += numbers[-2]`
会读 `rbp-52`，但读是安全的）。这就是它能稳定复现的原因。

## 两个坑

- **`accum` 会挡住你**：任何一次 `accum` 等于 67 都会再触发一次 skip，把 `i` 顶飞。
  所以除第一步外，每次都要根据快照里的 `accum` 决定下一个值（等于 67 就发 `1` 顶开）。
  exploit 里每条规则都是靠 SNAPSHOT 反馈驱动的。
- **flag 可能和最后一个快照粘在同一个 TCP 包里**：第一版 exploit 因为
  `recv` 一到 `rbp+00:` 就 break，把同一包里跟着的 flag 丢掉了，看起来像"没有输出"。
  修法是把收到的所有字节累积起来最后再搜。

## 复现

```sh
python3 exploit.py
# [+] FLAG: K17{maybe_the_true_reward_is_the_stacks_we_pwned_along_the_way}
```

## 修复建议

- 循环变量别让用户可控的索引越过数组：`for (int i = 0; i < SLOTS; )` 且**只在一处自增**。
  这里的根因不是"检查写得松"，而是 `i++` 出现了两次。
- 或者干脆用 `snprintf` 前先 `if (i < 0 || i >= SLOTS) break;`。
- 附带一提：`SNAPSHOT` 这个"调试工具"把栈直接摊给选手，把这道题从
  "需要 leak 才能 ROP" 降成了"读快照就能定位 `win` 和 `i`"。出题人显然是有意的，
  但线上环境保留这种调试后门很危险。
