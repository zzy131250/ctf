# shamir secret spilling — Writeup

**Flag**: `K17{0ur_cl1ent5_r3ally_d0nt_like_r0tating_their_keys!}`
**Category**: crypto · medium · 100 pts

## TL;DR

`Q` 和 `P` 在**同样那 16 个点**上取值相同，所以 `Q - P = R·Π`（`Π = ∏(x - x_j)`）。
把 `e := Q - P_pad` 的 32 个系数全部拉出来看，题目保证每个都 `< B = 2^273`，
而模数是 `2^512`。于是

```
A·e ≡ b  (mod MOD)        A 是 24×32 的 Vandermonde（16 个已知 + 8 个新点）
```

`e` 落在一个行列式为 `MOD^24` 的 32 维格的陪集里。陪集里"随机"向量的长度约
`MOD^(24/32) = 2^384`，而真的 `e` 只有 `2^276` —— **这个 2^108 的落差就是全部突破口**。
Kannan embedding + LLL 一把出。

## 题目结构

```python
assert len(P) == 16        # deg P < 16，16 个 share 可完全恢复
assert len(Q) == 32        # deg Q < 32，需要 32 个 share
assert len(known) == 16    # 泄露的旧 share
assert len(new) == 8       # 新发的 share
# 加起来 24 < 32，差 8 个
```

关键的两行：

```python
for x, px in known:
    assert polynomial_eval(P, x) == px
    assert polynomial_eval(Q, x) == px      # <-- 同一批 share 对 Q 也成立
...
for pc, qc in zip(P + [0] * 16, Q):
    assert abs(centered(qc - pc)) < B       # <-- 系数级别的小误差
```

这就是"backwards compatible"的代价：新多项式被绑死在旧多项式附近。

`B` 有 273 bit，`MOD` 有 512 bit —— 误差占模数的 53%，看着很大，但对格来说够小了。

## 解法

**第一步：恢复 P。** 16 个 share + deg < 16 → Lagrange 插值，唯一确定。已验证 16 个点全中。

**第二步：建立关于 e 的线性系统。** 令 `T = P + [0]*16`（补零到 32 项），`e = Q - T`。
则 `Q = T + e`，代入 24 个已知求值点：

```
A·(T + e) ≡ y   →   A·e ≡ y - A·T =: b   (mod MOD)
```

**第三步：求短向量。** `A` 是 24×32 满秩，`e` 的解集是一个秩 32 格的陪集：

- 对 `A` 做模 `MOD` 的 RREF → 24 个 pivot 列、8 个自由列
- 格基 = `{MOD·e_p : p 是 pivot 列}` ∪ `{每自由列对应的零空间向量}`
- 格行列式 `= MOD^24 = 2^12288`，32 维 → 特征尺度 `2^384`
- 目标向量 `-e0`（特解）到格的期望距离 `≈ 2^384`

而真 `e` 的 `|e|∞ < 2^273`，`|e|₂ ≈ 2^276` —— 比特征尺度短 **2^108**。
Kannan embedding 构造 33 维格（把 target 拼进去、加一列常数 `B`），LLL 直接把它挑出来。

**第四步：** `Q = T + e`，flag 就是 Shamir 的 secret `Q(0) = Q[0]`。

## 实测输出

```
[*] MOD bits=512  B bits=273
[*] P recovered (deg < 16), verified on all 16 leaked shares
[*] 24 pivotal columns, 8 free columns
[+] short vector found (mpfr precision=1024)
[*] |e|_inf bits: 267  (bound 273 )
[*] Q verified on all 24 shares

[+] secret -> b'K17{0ur_cl1ent5_r3ally_d0nt_like_r0tating_their_keys!}'
```

`|e|∞` 实测 267 bit，卡在 273 的界内 —— 说明模型理解正确。
最后在**全部 24 个 share** 上重验了 `Q`，不是"解出来就用"。

## 环境坑

这台机器上 `pip install fpylll` 会先成功编译、但 `import` 时报
`ModuleNotFoundError: No module named 'cysignals'` —— 得补一句：

```sh
pip3 install --user fpylll cysignals
```

另外 fpylll 的 `LLL.reduction` 指定 `float_type="mpfr"` 时**必须同时指定 `method`**
（`'proved'`/`'fast'` 等），否则落在 wrapper 分支报
`ValueError: LLL wrapper function requires float_type==None`。

精度用 `precision=1024` 就够（512 bit 的模数 + 33 维）。脚本里写了
1024 → 2048 → 4096 的重试阶梯，实际第一次就命中。

## 修复建议

- 旧的 share 不该在新方案里继续有效 —— 这正是"backwards compatible"的代价。
  应该重新分发全新 share（题目 flag 本身就在吐槽这点）。
- 更根本地：**共享同一个多项式**的方案里，泄露 24 个点而只差 8 个，再叠加"系数接近旧值"
  这个额外信息，等于把 8 个自由度用小误差界的格攻击直接吃掉。要么换模数/域，
  要么让 `B` 小到 `2^(512/4)` 以上（即误差不能显著小于 `MOD^(1/4)` 量级的格期望值），
  要么彻底不复用旧 share。
