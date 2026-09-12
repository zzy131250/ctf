# leaky rsa — Writeup

**Flag**: `K17{th3_t1tan1c_sh0uldv3_us3d_duct_t4p3}`
**Category**: crypto · easy · 100 pts (239 solves)

## TL;DR

`leak = dp + dq`，其中 `dp = d mod (P-1)`、`dq = d mod (Q-1)`，`e = 257` 很小。
由 `e·dp ≡ 1 (mod P-1)` 得 `e·dp = 1 + kp·(P-1)`（`1 ≤ kp ≤ e-1`），对 `dq` 同理：

```
e·leak - 2 = kp·(P-1) + kq·(Q-1)
          =>  kp·P + kq·Q = e·leak - 2 + kp + kq  =: C
```

联立 `P·Q = N` 消元得 `-kp·P² + C·P - kq·N = 0`，判别式
`D = C² - 4·kp·kq·N` 必须是**完全平方**。`kp, kq` 各只有 256 种，暴力两重循环
（2^16 次 `isqrt`）即可唯一定出 `(P, Q)`。之后就是普通 RSA 解密。

## 题目结构

```python
e = 257
phi = (P - 1) * (Q - 1)
d = pow(e, -1, phi)
dp = d % (P - 1)
dq = d % (Q - 1)
dsum = dp + dq            # 泄露的是两者的“和”
f.write(f"leak = {dsum}\n")
```

单看 `dp` 或 `dq` 都是标准部分私钥泄露攻击（`1 < e < 2^16`，穷举 `k` 后
`gcd(e·dp - 1, N)` 即得因子）。但这里泄露的是 `dp + dq`，所以要**同时**穷举两个
乘数 `kp, kq`，并把「两个未知数」化成关于 `P` 的一元二次方程。

## 关键脚本片段

```python
# e*dp = 1 + kp*(P-1),  e*dq = 1 + kq*(Q-1)
base = e * leak - 2
for kp in range(1, e):          # 1..256
    for kq in range(1, e):      # 1..256
        C = base + kp + kq      # = kp*P + kq*Q
        D = C * C - 4 * kp * kq * N
        if D < 0:
            continue
        s = math.isqrt(D)
        if s * s == D:          # 判别式是完全平方 -> 整数解
            P = (C + s) // (2 * kp)
            if N % P == 0:
                Q = N // P
                ...
```

实测命中 `kp = 230, kq = 135`。

## 实测输出

```
[+] kp=230 kq=135
[+] P bits=1024 Q bits=1024
[+] leak verified (dp+dq == leak)
[+] flag -> b'K17{th3_t1tan1c_sh0uldv3_us3d_duct_t4p3}'
```

注意脚本解出 `(P, Q)` 后**重算** `d = e^{-1} mod phi`、`dp = d mod (P-1)`、
`dq = d mod (Q-1)` 并断言 `dp + dq == leak`，确认因子正确再去解密 —— 不是
"解出因子就用"。

## 环境 / 性能

`kp, kq ∈ [1, 256]` 共 65536 次迭代，每次一个约 2048 bit 的 `math.isqrt`。
单核 1 vCPU 上数秒内跑完，无内存压力。纯标准库（`math.isqrt`）+ `pycryptodome`
的 `long_to_bytes`，不需要格工具。

## 修复建议

`e` 取太小（257）让 `k = (e·dp - 1)/(P-1)` 只剩 256 种可能，这是所有
"泄露 dp/dq" 类攻击的根源：**e 必须够大**（如 65537 只让枚举到 2^16，仍然可攻，
但配合"泄露的是和而非单个值"才有本题的价码）。更根本地，CRT 加速参数
`dp, dq` 是私钥的等价物，任何时候都不该输出；连"部分信息"（和、差、高位）
都不行。应使用恒定时间、无泄露的 RSA 实现，或直接不导出 CRT 参数。
