# Evilgram — Writeup

**Flag**: `K17{y0u_Th0ug5t_W3_w3Re_Ev1l_bUt_re4llY_we_are_JuSt_m4ss1ve_cH1cken_l0vers_w1th_a_huge_Hung3r_anD_n0th1ng_cAn_sT4nD_1n_OuR_way!!}`
**Category**: rev · medium · 100 pts (152 solves)
**附件**: `handout.zip` → `evilgram/evilgram.html`（303,884 bytes）

## TL;DR

附件是一个 Evilgram 聊天记录的静态快照。其中 "John Wick" 的对话里嵌了一条**带 Plotly
3D 体素动画**的消息（"一直在变的奇怪消息"），同一段 HTML 里还夹着一份 `<pre>` 包裹的
Python 源码 —— 那就是生成这条动画的脚本。

脚本干的事：

```
message.txt --(encode_msg_to_ruleset)--> ruleset(0..255 的一个排列)
            --(generateHist, 128 步)--> hist[0..127]  # 每帧 4×4×4 二值体素
            --(gen_plotly)--> message.html          # 128 帧的 Plotly 动画
```

这是一个 **256 状态的 2×2×2 分块细胞自动机**：每一步读一个 2×2×2 块的 8 bit 状态 `s`，
把 `ruleset[s]` 当作新状态写回。整个 4×4×4 地图每一步被 8 个块**全部**覆盖（步号决定
分块的偏移），所以 127 次状态转移 × 8 块 = **1016 个 `(s, ruleset[s])` 观测**，足以
恢复**完整的 ruleset 排列**。

拿到排列后，把它当作 `encode_msg_to_ruleset` 的 Lehmer/factoradic 编码反解，
直接得到明文，flag 就在里面。

全程离线，不需要连 `https://evilgram.unswsecsoc.workers.dev`（该域名在本次环境里
DNS 被污染 + SNI 阻断，打不通；也不需要它）。

## 1. 先看附件里有什么

```
evilgram.html
├── 5 段聊天记录（Anton Chigurh / John Wick / The Boys / LIVECon Group Chat / Customer Support）
├── <script src=".../plotly-4.0.0.min.js">          ← 只有 Plotly 在 CDN 上
├── <div id="157116db-…" class="plotly-graph-div">  ← 1 个 Plotly 图
│     ├─ Plotly.newPlot(…, [Mesh3d …])              ← 初始帧（= hist[0]）
│     └─ Plotly.addFrames(…, [ …128 个 frame… ])     ← hist[0..127]
└── <pre>…12,944 字符的 Python 生成脚本…</pre>        ← 藏在 "John Wick" 的消息里
```

聊天记录本身是干扰项（Customer Support 那段是 LLM 风味的废话），有用的只有
Plotly 数据 + 那段 Python。把 `<pre>` 里的源码抠出来就是题目逻辑。

## 2. 关键代码

### 2.1 消息 → ruleset（可逆的 factoradic 编码）

```python
def encode_msg_to_ruleset(msg):
    msg_bytes = msg.encode('utf-8')
    msg_num = int.from_bytes(msg_bytes, 'big')

    if msg_num >= math.factorial(256):
        print("Flag too long (~210)"); exit(1)

    factoradic = []
    for i in range(256):
        msg_num, rem = divmod(msg_num, i+1)
        factoradic.append(rem)
    factoradic.reverse()

    l = list(range(256))
    ruleset = []
    for skip_count in factoradic:
        ruleset.append(l.pop(skip_count))
    return ruleset
```

就是把整条消息当成一个大整数，做**阶乘进制（factoradic）**分解，得到 256 个
Lehmer-code 数字 `d_0..d_255`（`d_i < i+1`，`d_i` 是第 `i` 位的"跳过数"），
然后从 `[0..255]` 里依次 pop 出 `d_j` 指向的元素。反过来：
`ruleset[j]` 在剩余列表里的下标 → `d_{255-j}` → `num = Σ d_i · i!` → 大端字节串 = 明文。

注意注释 `# Flag too long (~210)`：`256!` 大约对应 210 字节的消息，而实际解出的明文
正好是 **210 字节**（flag 前面还有一句废话 "please i NEED the kfc recipe ASAP…"）。
题目是把 flag 包在一段自然语言里发的，不是单独一个 flag。

### 2.2 细胞自动机（`generateHist` / `step_forwards`）

```python
BLOCKSTATES = [ ((a,b,c,d),(e,f,g,h)), … ]   # 256 项，第 k 项就是状态 k 的 8 个 bit

def generateHist(ruleset, historySize, mapSize, seed=None):
    if seed == None:
        seed = int(time.time())              # ← 种子是生成时刻，不可复现（但初始帧在动画里）
    map = initArr((mapSize,)*3, seed)        # 4×4×4，随机 0/1
    hist = initArr((historySize,)+ (mapSize,)*3, seed)
    steps = 1
    while steps <= historySize:
        hist[steps-1:steps] = map            # 先记录，再演化
        step_forwards(map, ruleset, steps)
        steps += 1
    return hist

def step_forwards(map, rules, step):
    # 4×4×4，循环只跑 2×2×2 = 8 个块；块的"角"由 step 的 3 个 bit 决定
    for z in range(zSize >> 1):
        for y in range(ySize >> 1):
            for x in range(xSize >> 1):
                bx = x*2 + (step&1)
                by = y*2 + ((step&2)!=0)
                bz = z*2 + ((step&4)!=0)
                s = calcBlockState(map, bx, by, bz)
                setBlockState(map, bx, by, bz, rules[s])
```

- `calcBlockState` 把 2×2×2 的 8 个格子按 (`z,y,x`)→LSB 的顺序拼成 0..255 的状态号，
  索引全部 `% 4` 环绕。
- `setBlockState` 把 `BLOCKSTATES[state]` 的 8 个 bit 原样写回 —— 所以**一个块的
  "新状态"就等于 `rules[旧状态]`**，新旧状态都能从相邻两帧直接读出。
- `(step&1, step&2, step&4)` 只决定块的**角点偏移**；由于 `x` 也遍历 `{0,1}`，
  `x*2 + (step&1)` 覆盖 `{1,3}` 或 `{0,2}` —— **每一步 8 个块恰好铺满全部 64 个格子**，
  也就是每一步整张图都被重写一次。

### 2.3 动画渲染（`gen_plotly` / `build_voxel_mesh`）

```python
cube_vertices = [[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]]
offsets  = np.stack([x, y, z], axis=1)              # np.where(data==1)，按 z,y,x 排序
vertices = (offsets[:,None,:] + cube_vertices).reshape(-1,3)
padded   = np.full((max_voxels*8, 3), 0)            # 补 (0,0,0) 到 max_voxels=42
```

每个 voxel 贡献连续 8 个顶点，**第 0 个就是 voxel 原点 `(x,y,z)`**。`Mesh3d` 的
`i/j/k` 面索引对补齐后的顶点做 `+8k` 偏移，所以补齐出来的 `(0,0,0)` 只会画成
退化三角形，不影响还原 —— 但解析时要记得**把尾部连续的一串 `(0,0,0)` 丢掉**，
否则每一帧会凭空多出 / 少掉坐标原点那一格，导致 ruleset 出现矛盾
（第一版就是这样拿到 128 个冲突的）。

## 3. 解题步骤

### 3.1 抠数据

```python
d = open('evilgram.html').read()
i = d.find('Plotly.addFrames'); start = d.find('[', i)
# 括号配平找到数组结尾，json.loads → 128 个 frame，每个 frame.data[0] 有 x/y/z
```

`newPlot` 的初始帧和 `frames[0]` 逐字节相同（`np.array_equal` 为 True），
说明 `frames[k] == hist[k]`，帧序就是时间序。

### 3.2 帧 → 4×4×4 二值图

对每帧取 `x[::8], y[::8], z[::8]` 得到 voxel 原点列表，去掉尾部 `(0,0,0)` 的
padding 段，置 1。得到 `maps[0..127]`，每帧 21~42 个 1。

### 3.3 恢复 ruleset

```python
for step in range(1, 128):
    ox, oy, oz = step & 1, (step >> 1) & 1, (step >> 2) & 1
    for xb in (0,1):
      for yb in (0,1):
        for zb in (0,1):
            x, y, z = xb*2+ox, yb*2+oy, zb*2+oz      # 注意 calcBlockState 的参数序是 (x,y,z)
            s = block_state(maps[step-1], z, y, x)     # 演化前
            t = block_state(maps[step],   z, y, x)     # 演化后 = ruleset[s]
            rules[s] = t
```

结果：**256 个状态全部被观测到，0 冲突**，且像集正好是 `0..255` —— 确认它就是
那个双射排列。

### 3.4 反解 factoradic

```python
l = list(range(256)); digits = [0]*256
for j in range(256):
    sk = l.index(ruleset[j]); digits[255-j] = sk; l.pop(sk)
num = sum(dd * math.factorial(i) for i, dd in enumerate(digits))
msg = num.to_bytes((num.bit_length()+7)//8, 'big')
```

（正向再编码一遍 `msg` 得到完全相同的 `ruleset`，闭环验证。）

### 3.5 输出

```
please i NEED the kfc recipe ASAP my local kfc closed down and I NEED MY CHICKEN
K17{y0u_Th0ug5t_W3_w3Re_Ev1l_bUt_re4llY_we_are_JuSt_m4ss1ve_cH1cken_l0vers_w1th_a_huge_Hung3r_anD_n0th1ng_cAn_sT4nD_1n_OuR_way!!}
```

明文长度 **210 字节**，正好是源码注释里 `Flag too long (~210)` 的上界，说明整条
message 就是这一句。

## 4. 验证

1. **CA 重放**：用恢复出的 ruleset + `maps[0]` 作为初值，按 `step_forwards` 的语义
   重跑 1..127 步，与动画的 128 帧**逐格完全一致**（`np.array_equal` 全部 True）。
2. **编码闭环**：把解出的明文重新 `encode_msg_to_ruleset`，得到的排列与从动画恢复的
   `ruleset` **逐元素相同**。
3. `ruleset` 是 0..255 的双射（`sorted(values) == list(range(256))`）。

`solve.py`（本目录）把 1~3 步串成一条命令：

```
$ python3 solve.py evilgram.html
please i NEED the kfc recipe ASAP my local kfc closed down and I NEED MY CHICKEN K17{...}
```

## 5. 环境坑 / 备注

- **服务打不通**：`evilgram.unswsecsoc.workers.dev` 在本机 DNS 被解析到
  Facebook/Yahoo 段（如 `173.255.213.90`），443 直接被丢包；本机只有 80 端口
  对少数白名单域可用。这道题**纯离线可解**，服务只是同一份页面（"live" 版），
  不需要它。
- 题目说"消息一直在变"指的就是这个 128 帧动画 / 每步整图重写的 CA。
- 一个容易翻车的点：`padding` 的 `(0,0,0)` 顶点。少了这步处理，`ruleset` 会出现
  大量矛盾（每帧都会污染坐标原点那一格所属的块）。

## 6. 修复建议

- 这题的"加密"是**双射 + 公开的 128 帧动画**：整个 ruleset 是完全可观测的，
  127×8 次观测就能唯一的确定排列，等价于把明文直接放在附件里。想让"一直在变的消息"
  真的有密码学意义，至少应让块状态不可被完整恢复（例如只发布部分帧、随机丢弃更新、
  或真正的密钥流 + 单向性）。
- 另外把生成脚本以 `<pre>` 明文形式塞在同一条聊天消息里，等于连逆向前提都送给了选手。
