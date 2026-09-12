# close enough — Writeup

**Flag**: `SCONES{y0u_got_m3_out_of_a_p1ckle}`
**Category**: forensics · easy · 100 pts (219 solves)
**附件**: `out.pkl.part` (376 B), `ekv.py`

> 注意：本题 flag 前缀是 `SCONES` 而不是 `K17`（README 明确注明）。

## TL;DR

```python
raw  = open('out.pkl.part','rb').read()
body = raw[:2] + raw[11:]                    # 去掉 FRAME 头
cut  = body.index(b'\x8c\x21admin password') # 丢掉被截断的第 4 个 key
obj  = pickle.loads(body[:cut] + b'uub.')    # SETITEMS, SETITEMS, BUILD, STOP
print(obj['the flag'])                       # SCONES{y0u_got_m3_out_of_a_p1ckle}
```

关键点：`secret` **就明文存在 pickle 里**，所以不用恢复任何密钥——
只要把截断的 pickle 补完，就能直接调用题目自带的 `__getitem__` 解密。

## 题面要点

`ekv.py` 是一个异或加密的 KV 容器：

```python
class EncryptedKV:
    def __init__(self, secret):
        self.secret = secret
        self.d = {}

    def __getitem__(self, key):
        num: int = (self.d[key] ^ self.secret)
        return num.to_bytes(-(num.bit_length() // -8)).decode()

    def __setitem__(self, key, value):
        self.d[key] = int.from_bytes(value.encode()) ^ self.secret
```

- 存：`enc = int.from_bytes(plaintext, 'big') ^ secret`
- 取：`plaintext = (enc ^ secret).to_bytes(ceil(bitlen/8))`（`to_bytes` 省略
  `byteorder`，在 Python 3.11 之前默认 `'big'`；本机 3.11+ 必须显式补上）

`out.pkl.part` 是这样一个对象的 pickle，下载到一半断了（"got stuck halfway
through"）。

## 思路

### 1. 先看截断到底截掉了什么

`pickletools.dis()` 一边 dis 一边报错，但能看清结构：

```
   2: \x95 FRAME      416        <- 声称帧长 416，文件只有 376 字节
  36: STACK_GLOBAL   __main__.EncryptedKV
  43: MARK
  44: 'secret'  \x8a LONG1 ...    <- 密钥，明文躺在文件里
 100: 'd'  {  (MARK
 107:   'the three digits on the back of my credit card' -> LONG1
 203:   'an album you should listen to'                  -> LONG1
 282:   'the flag'                                       -> LONG1
 340:   'admin password for the scoreboard'   <- 只有 key，value 被截掉了
DIS ERROR: pickle exhausted before seeing STOP
```

所以文件里共有 4 个 `LONG1` 载荷（1 个 secret + 3 个完整 value）。**flag 那个
entry 是完整的**，被截断的只是第 4 个 value（scoreboard 管理员密码），而它对本
题无用。

### 2. 把 pickle 补完

两处可以手工修复，都不需要猜数据：

1. **FRAME 头对不上**：`\x95` + 8 字节声明了 416 字节的帧，但实际只剩 376。
   协议 4 的 FRAME 只是缓冲提示，直接删掉这 9 个字节（`raw[:2] + raw[11:]`）
   让 Unpickler 顺序读下去即可。
2. **inner dict 没闭合**：最后一个 `MARK`（内层 dict 的 item 起点）之后少了
   `SETITEMS`，内层 `d` dict 和外层对象 `__dict__` 也各差一个 `SETITEMS`，
   对象还差 `BUILD` 和 `STOP`。

去掉那个没有 value 的第 4 个 key 后，按 pickle 协议手工补上：

```python
rebuilt = body[:cut] + b'u' + b'u' + b'b' + b'.'
#                        ^    ^    ^    ^
#          SETITEMS(内层d) │    │    STOP
#              SETITEMS(外层__dict__) BUILD
```

> `b'uub.'` 顺序要对：先关内层 dict、再关外层 `__dict__`，最后 `BUILD`+`STOP`。

### 3. 解密

无需暴力、无需已知明文。`secret` 就在 pickle 里，直接交给原始逻辑：

```python
class EncryptedKV:  # 抄 ekv.py，仅把 to_bytes 的 byteorder 显式写成 'big'
    def __init__(self, secret): self.secret = secret; self.d = {}
    def __getitem__(self, key):
        num = self.d[key] ^ self.secret
        return num.to_bytes(-(num.bit_length() // -8), 'big').decode()
    def __setitem__(self, key, value):
        self.d[key] = int.from_bytes(value.encode(), 'big') ^ self.secret

obj = pickle.loads(rebuilt)
for k in obj.d:
    print(k, '->', obj[k])
```

输出：

```
the three digits on the back of my credit card -> '067'
an album you should listen to                  -> 'Mercurial World'
the flag                                       -> 'SCONES{y0u_got_m3_out_of_a_p1ckle}'
```

（`067` 和 `Mercurial World` 是 flag 里的彩蛋，不是提交项。）

## 实测

```
$ sha256sum out.pkl.part
4a41b48105789793c8837ddbfaaa338f9d5aaeaa573d946f4d333a621f5cdbb2  out.pkl.part
```
与 README 给出的 hash 一致 —— 附件完整未损坏，只是被人为截断。

round-trip 自检：把解出的明文用 `__setitem__` 重新加密，得到的整数 `to_bytes(45,'little')`
与文件里三个 `LONG1` 载荷**逐字节相同**，说明 secret 和明文都恢复正确：

```
'the three digits on the back o'   exact-match=True
'an album you should listen to'    exact-match=True
'the flag'                         exact-match=True
```

复现脚本：`solve.py`

## 坑 / 注意

- `int.to_bytes(length)` 省略 `byteorder` 在 **Python 3.11+ 已报 TypeError**
  （3.11 起强制要求）。原件能跑是因为作者用了旧版本；补上 `'big'` 即可，
  语义与旧默认值一致。
- 别把它当成"异或密钥恢复"题：secret 是明文的，且 45 字节的 secret 远长于
  最长的 plaintext（34 字节），靠 `enc1 ^ enc2` 消掉 secret 反而走偏。
- 第 4 个 entry 的 value 确实无法恢复（异或密钥流 + 未知明文），但也不需要。

## 修复建议

- 别把密钥和被加密的数据序列化到同一个对象里 —— `pickle` 出来的 `secret`
  属性是明文，等于没加密。
- 用 AEAD（AES-GCM / ChaCha20-Poly1305）替代裸 XOR；裸 XOR 下已知明文（如
  `SCONES{` 前缀）会直接泄漏密钥流。
- 传输大对象时带上完整性校验（长度/hash），别让半截文件还能被"补完"解析。
