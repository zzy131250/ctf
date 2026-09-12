# P = NP — WRITEUP

**Flag: `K17{i_have_discovered_a_truly_marvellous_flag_which_this_box_is_too_simple_to_contain}`**

## 题面

"I accidentally used black highlighter on the important part" —— 一篇 P=NP 的"论文" PDF，
关键部分被黑条盖住了。

## 解法

PDF 只有 1 页。要点是**黑条不是画上去的矩形，而是一张内嵌图片**（以及条上那句白字
`this part of the proof is too dangerous to be shown`）：

```
page.get_drawings()  -> 一个 428 x 63.5pt 的黑色填充矩形 @ (84,454)   # 看上去像黑条
page.get_images()    -> xref 19: 1612x132 DeviceRGB, 'Im1'            # 真正藏东西的地方
```

把这张图 dump 出来就是答案（白底黑字，不用做任何对比度增强）：

```
This proof is left as an exercise to the reader. Hint:
K17{i_have_discovered_a_truly_marvellous_flag_which_this_box_is_too_simple_to_contain}
```

一句话：**PDF 里"被涂黑"的内容要先看看它到底是矢量矩形还是独立 XObject 图片**——
如果是图片，直接 `extract_image` 就出来了，压根不用管图层顺序。

## 复现

```python
import fitz
doc = fitz.open('p-equals-np.pdf')
open('im1.png', 'wb').write(doc.extract_image(19)['image'])   # xref 19
```

依赖：`pip3 install --user pymupdf`（本机没装 poppler-utils，也没有 pdftotext/qpdf）。
