# cryjail — WRITEUP

**Flag: `K17{yaaaaaaay_i_h0pE_yoU_D1dn7_cra5H_0Ut!!!!!!!!!!!}`**

> 连接：`nc <host> <port>`，先问 `password:`，输实例口令（每队不同）。

## 题面

`chall.py`：`KEY = get_random_bytes(16)`（每连接随机），循环读 `iv:ciphertext`（hex），
`AES-CBC` 解密得到 `name`，然后把它拼进一段生成的 Python 源码：

```python
print(b"IMPLANTING ... AS: " + escape(name) + "!", file=devnull)
```

写进 `/tmp/run.py` → fork → 子进程 `compile()` + `exec()`，父进程只回报
`[ok] reported name to our database` 或 `[!] probably not enough cores or something idk lmao`。
flag 在容器 `/flag`（Landlock 只读整个 `/`，读得到）。
pwn.red/jail + Landlock 把文件系统锁成了只读、只在 `/tmp/run.py` 和 `/dev/null` 可写。

## 两个洞

### 1. `escape()` 放行 `"`

```python
SAFE = set(range(0x20, 0x7F))   # 注释还特意写：including '"' (0x22) and '\' (0x5c)
```

`escape()` 把不可打印字节转成 `\xNN`，但 `"` 是**可打印的**，原样落进 `b"...<name>!"`
字面量里 → 一个 `"` 就能提前闭合字符串，注入任意 Python 代码。

### 2. 密文不可控，但 **IV 可控** + 一个免费 oracle

`KEY` 是随机的，我们没法伪造明文。但是：

- **IV 是我们给的**，第一块明文 `P₁ = D(C₁) ⊕ IV`，等于一层**一次性密码本**——只是我们不知道 `D(C₁)`。
- **父进程把子进程的退出码告诉我们**：源码语法出错 → `compile()` 抛异常 → `[!] crushed`；
  正常跑完 → `[ok]`。

于是「名字里有没有一个没被转义的 `"`」就是一个 **1-bit oracle**（有 `"` → SyntaxError → crash）。
逐字节扫：固定 `C₁`，把 `IV[i]` 从 0 扫到 255 —— **唯一那个让 oracle 从 `[ok]` 翻成 `[!]` 的
`v` 就是 `v = D(C₁)[i] ⊕ 0x22`**，于是 `D(C₁)[i] = v ⊕ 0x22`。16 字节 ×256 次，13 秒收工。

细节：

- 探测时用 **两块** 密文 `(IV, C₁, C₂)`，其中 `C₂` 那一块的明文（= `D(C₂) ⊕ C₁`，先用 oracle
  确认它不含 `"`）当无害填充。**这样 `"` 永远不会落在名字最后一个字节上**——落在末尾会被模板
  的收尾引号"吃掉"变成合法拼接（`b"xx""!"` 是合法的隐式拼接），oracle 就不响了。
- 每块密文是独立解密的，所以**两块探测里学到的 `D(C₁)` 和单块密文里的一模一样** ✓。
- 服务是**往返延迟受限**（232ms/查询），但一次把 256 行 probe 全灌进去再收 256 个回复，
  就变成 **18ms/查询**（20 倍加速），整轮 13.8 秒。
- 校验：`name = 16 个空格` → `[ok]`（16 个字节全对才行）；`name = '"' + 15 空格` → `[!]` ✓。

拿到 keystream `R = D(C₁)` 后，想要明文 `P` 只需 `IV = R ⊕ P`。

## 3. 12 字节的 payload

模板是 `print(b"...AS: <NAME>!", file=devnull)` —— **注意 `!` 在收尾引号**前面**，
Python 里没有能"吃掉" `!` 的运算符，所以没法用 `or b` 之类的技巧收尾，只能自己把
`print(` 闭合再把剩下的注释掉：

```
NAME = ",breakpoint())#        ← 正好 16 字节
-->
print(b"IMPLANTING ... AS: ",breakpoint())#!", file=devnull)
```

`breakpoint()` 刚好 12 个字符，塞进 `",`+`)#` 的 4 字节外壳里。
`breakpoint()` → `pdb.set_trace()` → **pdb 直接在 socket 上开交互**（父进程此时阻塞在
`waitpid`，没人跟它抢 fd 0）。然后在 pdb 里：

```python
os.write(1, open('/flag','rb').read())     # os 是第 1 行 import 好的；os.write 无缓冲
c                                          # continue
```

```
> /tmp/run.py(3)<module>()
-> print(b"IMPLANTING NEURO LINK CHIP IN INDIVIDUAL IDENTIFIYING AS: ",breakpoint())#!", file=devnull)
(Pdb) K17{yaaaaaaay_i_h0pE_yoU_D1dn7_cra5H_0Ut!!!!!!!!!!!}52
```

## 踩过的坑

- **收尾方向搞反了**：一开始写成 `",breakpoint(),b`，以为模板收尾是 `!"`→ 实际是 `<name>!"`，
  `b` 后面直接跟 `!` → `b!` 不是字符串 → SyntaxError。本地 `compile()` 一下立刻现形，
  所以**生成器一定要在本地拿 `escape()` 复刻一遍再打远程**。
- 一开始以为要 16 字节塞下 `exec(input())`(13)+外壳，差一字节；换 `breakpoint()` 刚好。

## 文件

- `exploit.py` —— 完整利用（keystream 恢复 + payload 投递 + pdb 驱动），跑一次约 20 秒出 flag。
