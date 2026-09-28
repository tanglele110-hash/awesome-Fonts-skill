---
name: awesome-fonts-skill
description: 从中文字体目录按字形、正文或标题用途、样张简繁与来源信息选字，给出可核验的字体搭配和接入建议。Select Chinese typefaces from a curated catalog with evidence-aware pairing and implementation guidance.
---

# 中文字体选用 / Chinese font selection

根据实际设计任务使用 [data/fonts.json](data/fonts.json)，按需查看 [CATALOG.md](CATALOG.md) 的五类目录。数量和分类以数据文件为准。

Use the catalog for the requested design task. Read only relevant entries; the JSON is the source of truth for this package.

## 检索与选择 / Search and selection

在 Skill 所在目录执行，例如：

```sh
python scripts/fonts.py search --category serif --tag 正文
python scripts/fonts.py search 文楷
python scripts/fonts.py search --tag 海报 --tag 繁体 --json
```

结合用户已给出的用途、目标语言、尺寸与风格筛选；普通偏好可直接作合理假设。给出少量有差异的候选，说明主选字体、搭配角色、选择理由、来源链接和具体未验证项。

Filter using the brief's usage, language, size and style. Offer a small differentiated shortlist with a preferred choice, pairing role, rationale, source link and specific unknowns. Reuse information already supplied by the user.

## 证据边界 / Evidence boundaries

- `tags` 的正文、标题、海报是收藏时的设计判断；简体、繁体只描述现有样张，不能证明完整字库覆盖。`sampleText` 是文字内容，不是用该字体渲染的图片。
  Usage tags are design judgments; script tags describe the recorded specimen, not complete character coverage. Sample text is not a rendered specimen.
- `license` 记录已核对的许可、日期、证据链接与随包原文；逐款结果见 [LICENSE-REVIEW.md](LICENSE-REVIEW.md)。OFL 允许商用、修改和嵌入，但须保留版权与许可、遵守保留字体名，不可单独出售字体软件。使用完整字库时核对所下载版本的许可。
  The license fields contain the review date, source evidence and bundled text. Follow OFL copyright, naming and redistribution conditions. Check the license accompanying the exact full-font release you obtain.
- 仓库的 `assets/fonts/` 只含网页样张 WOFF2 子集；不得将其当作完整可用字体。安装或接入前，从核验过的来源获取完整字体，检查用户实际文字的字形覆盖。
  Only fixed specimen WOFF2 subsets are bundled for the gallery. Do not substitute these for a full font. Check the actual requested text against the selected font file.
- `latinSampleSupported` 只来自原样张记录；不能证明所有拉丁字符、标点或语言的覆盖。混排时标明中文字库和西文字库各自角色。
  Latin sample support is limited evidence, not full language coverage. Identify each font's role in mixed-script layouts.
- `family` 是记录名称；CSS 接入需以实际字体文件内部名称、字重与格式为准。生成建议可以继续；用户要求实现时再验证字体加载、fallback、缺字、移动端排版。
  Treat family names as recorded metadata. Verify the delivered font's names, weight and format, then test loading, fallback, glyphs and mobile layout when implementation is requested.

## 维护 / Maintenance

修改目录时阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，修改 JSON 后运行：

```sh
python scripts/fonts.py build
python scripts/fonts.py validate
```

Preserve stable IDs and variant distinctions. Do not add private paths, personal collection timestamps or browser state. Validate data and regenerate the catalog after an update. Repository publication and system installation follow the user's existing authorization.
