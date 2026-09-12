# cry-pto — Writeup

**Flag**: `K17{y0u_ar3_f1ll3d_w1th_deter1min4t10n}`
**Category**: beginner,crypto · 100 pts (244 solves) · remote: `nc chal.secso.cc 2000`

## TL;DR

签名方案是 **GF(2) 上的线性映射**：128×64 的 0/1 矩阵 `M`，签名就是
`sig(m) = M · m`（`m` 是 64 bit 消息列向量，运算在 GF(2) 上）。既然是线性的：

```
sig(a ⊕ b) = sig(a) ⊕ sig(b)
```

再结合每位单独求值时的线性（矩阵每行固定、消息位可叠加），有
**`sig(a ⊕ b) = sig(a) XOR sig(b)`**。服务端送我们一个免费样本
`sig(b"babyuser")`，只禁止查询 `root = b"chadr00t"` 本身。那就查
`q = user ⊕ root`（`q ≠ root`，合法），然后

```
sig(root) = sig(user) ⊕ sig(user ⊕ root) = user_sig XOR query_sig
```

拿这个 XOR 结果当 root 的签名提交即可。

## 题目结构

```python
for _ in range(TAG_SIZE * 8):            # 128 行
    self.matrix.append(int.from_bytes(os.urandom(MESSAGE_SIZE)))   # 每行 64 bit

def sign(self, message):
    msg_vector = int.from_bytes(message)     # 64 bit
    res = 0
    for row in self.matrix:
        res <<= 1
        res += (row & msg_vector).bit_count() % 2    # 内积 mod 2
    return res.to_bytes(TAG_SIZE)
```

第 `i` 位签名的值 = `⟨row_i, m⟩ mod 2`，这是 `m` 的**每个比特**的线性函数，所以
`sign` 是 `{0,1}^64 → {0,1}^128` 的线性映射。注意 `user` 和 `root` 都是
**8 字节**，正好等于 `MESSAGE_SIZE`，可以自由做 XOR 后再送进 `sign`。

服务端逻辑只用 `if query == root` 挡住"直接查答案"，没有挡住"查一个与之
线性相关的值"：

```python
user = b"babyuser"; root = b"chadr00t"
user_sig = sig.sign(user)            # 免费样本
query = bytes.fromhex(input("> "))
if query == root: sys.exit(0)        # 只挡完全相等
query_sign = sig.sign(query)         # 我们查 q = user ^ root
attempt = input("> ")                # 提交 user_sig ^ query_sign
if sig.verify(root, bytes.fromhex(attempt)): print(open("/flag").read())
```

## 关键脚本片段

```python
user, root = b"babyuser", b"chadr00t"          # 都是 8 字节
q = bytes(a ^ b for a, b in zip(user, root))   # q != root，不会被拦
# ... 读 user_sig，发 q，读 query_sig ...
attempt = bytes(a ^ b for a, b in zip(user_sig, query_sig))
# 提交 attempt.hex() -> /flag
```

完整脚本见同目录 `exploit.py`（纯 `socket`，无第三方依赖）。

线性关系也做过本地复现验证：用同构的本地 `CRYSig` 随机实例，
`sig.sign(root) == sig.sign(user) XOR sig.sign(user^root)` 恒成立。

## 实测输出

```
[*] user signature: c56c1491254b8bc4af99228ec31b05e7
[*] > your signature: 3d21c31fdb8c308922efd19075dfaec5   (q = 0109031d07435506)
[*] forged root sig = f84dd78efec7bb4d8d76f31eb6c4ab22
[*] response: > K17{y0u_ar3_f1ll3d_w1th_deter1min4t10n}

[+] FLAG: K17{y0u_ar3_f1ll3d_w1th_deter1min4t10n}
```

## 环境 / 性能

无计算量，一次 TCP 交互即可（3 行输入输出）。本机是 aarch64 且 `python3` 为
3.9（`int.bit_count()` 不存在、`int.from_bytes` 需要显式 `byteorder`），但那些
只影响**本地复现**：攻击脚本本身只用 `socket` 和字节 XOR，不受影响。

## 修复建议

- 线性 MAC 天然可延展：任何"已知 `(m, tag)` 就能伪造 `m'`"的方案都不能用。
  这里 `sig(a⊕b) = sig(a)⊕sig(b)` 直接给出伪造。
- 只做"黑名单式"的相等检查（`query == root`）挡不住代数关系。应该用
  **随机化/非线性**的 MAC，例如 HMAC-SHA256（带密钥的 PRF），或者对
  **消息做去相关**（如先哈希再签名、加 nonce/计数器）。
- 若确实要用矩阵构造，至少给秘密矩阵加随机化掩码（类似 LPN/LWE 的
  `M = A·S + E`），让单次查询不能线性解出目标签名。
