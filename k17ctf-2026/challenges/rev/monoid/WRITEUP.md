# monoid — Writeup

**Flag**: `K17{a_M0NaD_1s_4_M0n0Id_1n_th3_c4t3gORy_0f_3Nd0FuNC70r5}`
**Category**: rev · medium · 100 pts (173 solves)
**Author**: m0wiii

## TL;DR

题目给的是一个 Haskell 程序（GHC Core dump，不是可执行文件）和一个 ASCII 渲染出来的
分形 `out.txt`。程序流程极短：

```
out.txt = renderJulia(params)
params  = map read (words (decipher (fromHex HEX) "#!s3kur1ty"))
```

`params` 是 5 个空格分隔的数字（cx cy maxIter width height），而 `decipher` 解出来的
**字符串第一个 token 就是 flag**（程序里 `_` 匹配后直接丢弃，Dead binding）。

解密是两个 8-bit 字节级操作：`xor` 再减 67（mod 128）。

```
flag + " -0.745643887 0.113825904 180 96 32"
```

## 题目结构（三个模块）

`Main.dump-simpl` 是 GHC 的 Tidy Core dump，Tidy 之后所有函数体都是显式的 `\x ->` lambda
和 `case`，读起来比汇编容易得多。

### `Decode.hs`

```haskell
xorChar a b  = chr (ord a `xor` ord b)
unsubsChar a = chr ((ord a - 67) `mod` 128)      -- 67 = ord 'C'

decipher ct key
  | null key  = error "boop"
  | otherwise = zipWith (\c k -> unsubsChar (xorChar k c)) ct (cycle key)
```

注意参数顺序是 `unsubsChar (xorChar k c)`：**key 是 `xorChar` 第一个参数**，
但因为 xor 对称所以等价于 `c ^ k`。`cycle` 让 key 无限重复（key = `#!s3kur1ty`，9 字符）。

`fromHex` 就是两两配对的 hex 解码，`odd (length input)` 或奇数个 nibble 就
`error "..."`（本题无用）。

### `Fractal.hs`

标准 escape-time Julia 集渲染，**参数是 (cx, cy)，即 Julia 常数 c**，初值 z0 由像素坐标决定：

```haskell
palette = " .-:=+*#%@"

renderJulia cx cy maxIter width height =
  unlines [ [ palette !! min 9 ((n * 10) `div` (maxIter + 1))
            | x <- [0 .. width  - 1]
            , let z0r = -1.8 + 3.6 * fromIntegral x / fromIntegral (width  - 1)
                  z0i = (-1.0 + 2.0 * fromIntegral y / fromIntegral (height - 1)) * 0.5
                  n   = go 0 (z0r :+ z0i) ]      -- go: |z|>2 或 n>=maxIter 就停
          | y <- [0 .. height - 1] ]
  where go n z | magnitude z > 2.0 = n
               | n >= maxIter       = n
               | otherwise          = go (n + 1) (z*z + (cx :+ cy))
```

细节：`magnitude z > 2.0` 的判断在 `n >= maxIter` **之前**，且初值 z0 也要先判一次，
所以返回的 `n` 是"逃逸前迭代次数"（0 表示 z0 本身就已逃逸）。颜色索引
`min 9 ((n*10) div (maxIter+1))` 把 `n ∈ [0, maxIter]` 映射到 0..9。

### `Main.hs`

```haskell
main = writeFile "out.txt" $
  (\ (a,b,c,d,e) -> renderJulia a b c d e) $
    case words (decipher (fromHex HEX) "#!s3kur1ty") of
      _ : r : i : m : w : h : [] ->
        (read r, read i, read m, read w, read h)     -- read @Double @Double @Int @Int @Int
      _ -> error ""
```

`words` 按空白切分，`_` 把**第一个 token**（就是 flag）丢掉，后面 5 个 token 才是
真实的分形参数。所以 flag 根本没被"用"，纯属藏在解密串里。

## 解法

没有加密强度，纯数据流还原。密文 hex：

```
2d55090d4f576242655d24030705490250210748502d54111f4450065f0f010704041d5f6024485b500851457a5201384c68255b000613351141070859560b4a1c03094a0e1a505007471d0e0749080a5442074818160e48170f56
```

key = `#!s3kur1ty`（9 字节），对每个字节 `c`：`p = c ^ key[i % 9]`，然后
`r = (p - 67) mod 128`。

```python
key = "#!s3kur1ty"
out = bytes(((c ^ ord(key[i % len(key)])) - 67) % 128
            for i, c in enumerate(bytes.fromhex(HEX)))
```

得到：

```
K17{a_M0NaD_1s_4_M0n0Id_1n_th3_c4t3gORy_0f_3Nd0FuNC70r5} -0.745643887 0.113825904 180 96 32
```

即 `cx = -0.745643887`、`cy = 0.113825904`、`maxIter = 180`、`width = 96`、`height = 32`。
`c = -0.745643887 + 0.113825904i` 是经典 Julia 集参数（题面说的 "really cool fractal"）。

## 验证

按 `Fractal.hs` 的语义用 Python 重写一遍（`render.py`），渲染结果与 `out.txt`
**逐字节完全一致**（`MATCH: True`），说明对初值范围 `[-1.8, 1.8] × [-0.5, 0.5]`、
逃逸半径 2.0、颜色映射的理解都正确 —— flag 也因此在语义上被交叉验证。

```
MATCH: True
```

## 环境坑

- `python3` 3.9，没有 `int.bit_count()`；`int.from_bytes` 要显式 `byteorder`（本题没用到）。
- 不需要跑任何二进制，纯静态阅读 + 30 行脚本。

## 修复建议

- 这题严格说不是 rev 而是 "读懂 Core dump 再 xor"。flag 直接明文躺在解密串里，
  连分形参数都不用真解出来就能拿 —— 若想提高难度，应该让 flag 由渲染结果决定
  （例如把 flag 藏在 Julia 集的某个特定像素/参数上），而不是和参数拼在同一个字符串里。
- 单字节 xor + 常数偏移在 2025 年（乃至任何时候）都不是加密；至少用 AEAD。
