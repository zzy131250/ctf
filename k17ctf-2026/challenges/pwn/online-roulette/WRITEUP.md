# online-roulette — Writeup

**Flag**: `K17{th1s_minib0lt_guy_must_b3_rlly_lucky_huh}`
**Category**: pwn · beginner · 100 pts
**Target**: `nc chal.secso.cc 4000`
**Exploit**: `exploit.py`（一键复现）

## TL;DR

`game()` 里那个“任意地址写一个字节”的原语其实**没有**挡住 `game` 自己的栈帧：
被写地址的上界是 `&wager = rbp_game-4`，而调用者传入的 `int *balance` 指针
正好被 spilled 在 `rbp_game-0x28`（比 `&wager` 低 0x24）——**可写**。

把这个指针的**最低字节**改掉，让它从 `&balance` 指向 main 的 `uint8_t name_length`
（`&balance-0x1d`）。第一次下注 `*balance -= wager` 就写进了 `name_length`：

```
name_length = (20 - 21) & 0xff = 0xff = 255
```

随后 main 里 `fgets(name, name_length, stdin)` 变成 255 字节、溢出 20 字节的
`char name[20]`，把 main 的 `int balance`（`rbp_main-4`）覆盖成 `0x7fffffff`，
直接满足 `if (balance > 999999999) win()`。

不需要 ROP、不需要覆盖返回地址、不需要猜 libc。

## 漏洞

```c
printf("[addr]> "); scanf("%lx", &addr);
if (addr > (uintptr_t)&wager) {        // 只挡住“更高地址”
    puts("intruder neutralised");
} else {
    printf("[value]> "); scanf("%u", &value);
    flush();
    *(unsigned char *)addr = (unsigned char)value;   // 任意 1 字节写
}
```

`addr` 只要是 `<= &wager` 就放行。栈向低地址增长，所以 `game` 自己的栈帧、
以及其中**保存的指针参数**全都在射程内。

```c
int balance = 10;      // main 帧
char name[20];
uint8_t name_length;

if (name_length > 20) exit(0);   // 检查过了，之后没人再看它
...
game(&balance);
...
fgets(name, name_length, stdin); // 长度变量可被游戏逻辑间接改写 -> 溢出
```

两处拼起来就是完整的利用链：**1 字节写 → 改写 `balance` 指针 → 改写 `name_length` → 栈溢出 → 改 `balance` 值 → `win()`**。

## 栈布局（本地 `x86_64-linux-gnu-gcc -O0 -fno-stack-protector` 复现，与远端快照一致）

`main`（`rbp_main`）：

| 变量 | 偏移 | 说明 |
|------|------|------|
| `int balance` | `rbp-0x4` | 最终要比 `> 999999999` |
| （填充） | `rbp-0xc .. rbp-0x5` | |
| `char name[20]` | `rbp-0x20 .. rbp-0xd` | `fgets` 目标，距 `balance` **0x1c = 28 字节** |
| `uint8_t name_length` | `rbp-0x21` | 紧贴 `name` 下方 |

`game`（`rbp_game`，`rsp = rbp_game-0x30`）：

| 变量 | 偏移 | 说明 |
|------|------|------|
| `int wager` | `rbp-0x4` | 就是写上界的 `&wager` |
| `unsigned int value` | `rbp-0x8` | |
| `unsigned long addr` | `rbp-0x10` | |
| **`int *balance`** | `rbp-0x28` (= `rsp+8`) | 保存着 `&balance = rbp_main-4`，**低于 `&wager`，可写** |

### 远端泄漏

题目给的调试工具（`SNAPSHOT()` = `int3` + ptrace）会把 `rsp[game] .. rbp[main]`
的栈窗口打印出来，形如：

```
=== camerons black magick ===
0x7ffff9818e10: 0x0000000000000001  <-- rsp [game]
0x7ffff9818e18: 0x00007ffff9818e7c          <-- 就是 spilled 的 &balance
...
0x7ffff9818e40: 0x00007ffff9818e80  <-- rbp [game]  (= rbp_main)
0x7ffff9818e48: 0x0000000000401566  <-- rsp [main]  (返回地址)
...
0x7ffff9818e80: 0x00007ffff9818f20  <-- rbp [main]
```

一次泄漏同时给出：

* `rbp_main` = `rbp [game]` 那一行存的值；
* `&balance` = 窗口里那个等于 `rbp_main-4` 的 qword 的值，而**它的槽位地址**就是
  写原语的目标（`rsp_game+8 = rbp_game-0x28`）。

所以 ASLR 完全不是问题。

## 利用步骤（一条连接内）

1. `name_length = 20`（合法最大值），拿到快照，解析出 `rbp_main`、`bal_slot`、`&balance`。
   *若 `(&balance & 0xff) < 0x1d` 则低字节改不到目标（会借位），重连换 ASLR。*
2. `addr = bal_slot`，`value = (&balance-0x1d) & 0xff` → `balance` 指针被重定向到 `name_length`。
3. `wager = 21` → `*balance -= 21` 把 `name_length` 从 20 变成 `0xff`，
   同时 `*balance < 0` 触发 `damn no more money` 提前返回 main。
4. `fgets(name, 255, stdin)` 收到 `b"A"*28 + p32(0x7fffffff)`：
   `balance = 0x7fffffff`，`win()` 打开 `/flag` 并 `puts`。

## 复现

```bash
python3 exploit.py
# [*] try #0 delta=0x1d off=0x1c
#     -> FLAG K17{th1s_minib0lt_guy_must_b3_rlly_lucky_huh}
```

脚本自带重连重试（处理低字节借位），单次成功率约 `(0x100-0x1d)/0x100 ≈ 86%`。

## 踩过的坑

* **重定向的偏移是 `0x1d` 不是 `0x21`。** `name_length` 位于 `rbp_main-0x21`，
  而 `&balance` 在 `rbp_main-4`，两者相差 `0x1d`。`*balance -= wager` 是 **4 字节 int**
  存储，只有把 `balance` 指到 `name_length` **本身**（而不是 `rbp_main-0x21` 之外的地方），
  这个 int 的最低字节才落在 `name_length` 上。指偏 4 字节时减法会落在 `name` 上方的填充区，
  `name_length` 保持 20，`fgets` 只读 19 字节，静默失败（本次第一轮就是这样失败的）。
* 覆盖 `balance` 只需 32 字节 payload，别写太长——`name` 上方 4 字节之后就是
  saved rbp / 返回地址，写爆会崩，虽然 `stdout` 无缓冲时 flag 仍可能先打出来。
* `win()` 读的是 `/flag`；远端 flag 前缀本题是 `K17{}`。
