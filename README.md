# MuskWords — 从马斯克帖子记录和学习英语

[网站](https://sukaidie.github.io/muskwords/) · 静态网页，Python 标准库构建，无 API 密钥或 npm 依赖。

## 当前收录与边界

目前收录 **50,873 条帖子、20,354 个不同候选词形、496,939 个词次**。

- 公开历史存档中的记录覆盖 **2010-06-04 至 2025-04-13**，另保留用户最初提供的 6 条 2026-11-06 样本。中间可能存在缺口，不代表每天或所有年份的完整发言。没有 2025-04-13 之后的完整历史采集服务。
- 按帖子 ID 去重，只提取原创正文和回复，不引入引用对象的 `quote` 正文或转发对象的 `retweet` 正文；排除转发标记为 true 或以 `RT @` 开头的记录，以及去除 URL / 提及后没有英文字符的记录。短回复如 “Yes” 也会纳入。
- 大小写合并，保留词形变化。例如 `work`、`works`、`working` 分开统计；保留缩写、专有名词、技术片段，不删除常见虚词。这是正则提取的**英文候选词形数**，含拼写错误、名称、缩写等，不等于词典词条数，更不能作为马斯克认识的总词汇量。
- **第三方存档尚未逐条与 X 原帖核对**。所有导入记录为 `sourceStatus: archive_record`、`verified: false`；用户原始样本为 `provided_sample`，也不继承 ZIP 中未经本项目独立确认的核验声明。旧存档不含官方对话字段，回复分类为文本推断；新存档优先使用其回复标记。
- 每条记录保存原帖 ID、X 链接、固定版本存档来源、`archiveDataset` 和从 0 开始的 CSV 数据行号 `archiveRow`。同 ID 重复记录保留先导入的来源与正文，不重复计算。
- 目前 740 个词有中文释义和人工参考等级，19,614 个仍显示“释义待核实 / 未标注”。CEFR 不是官方或词典认证等级；专有名词和未标注词不参与最低等级范围筛选。

## 数据来源与许可

| 来源 | 固定提交 | 原始记录 | 本库保留 |
|---|---|---:|---:|
| [MohrezSheikh/Elon-Musk-Tweets](https://github.com/MohrezSheikh/Elon-Musk-Tweets/tree/18bee13cf1acb251087343221478bf76ab45ee1a) | `18bee13cf1acb251087343221478bf76ab45ee1a` | 16,490 | 15,453 |
| [MagdalenaRomaniecka/Anatomy-of-a-Tweetstorm](https://github.com/MagdalenaRomaniecka/Anatomy-of-a-Tweetstorm/tree/7168f60757af7f7d1c8f85bcf9ddcb5d12ddef32) | `7168f60757af7f7d1c8f85bcf9ddcb5d12ddef32` | 55,099 | 35,414 个额外 ID |
| 用户 ZIP 样本（Elon Musk Archive 链接） | 每条记录附来源 | 6 | 6 |

第二个来源自述数据源于 Kaggle 的 `dadalyndell/elon-musk-tweets-2010-to-2025-march`，实际 CSV 最晚日期为 2025-04-13。它有 50,832 条符合导入规则的唯一帖子，其中 15,418 条与第一个来源重复。导入时不读取引用/转发对象的文本字段。

两份上游仓库的 MIT 许可分别保存在 [data/ARCHIVE-LICENSE.txt](data/ARCHIVE-LICENSE.txt) 和 [data/RECENT-ARCHIVE-LICENSE.txt](data/RECENT-ARCHIVE-LICENSE.txt)。这些仓库的许可不构成对第三方平台或帖子文字的独立授权；继续扩充时需核查对应来源的许可及平台访问条件。

## 功能

- 英文 / 中文搜索，按词频或字母排序；每页 60 个词。
- A1–C2 最低等级范围（如 B1 及以上、C1 及以上），以及单一等级筛选。
- 浏览器美式 TTS、本地收藏、CSV 导出。**导出当前所有匹配词，不限于当前页**。
- 单词详情显示总词次和关联帖子数；语境按帖子 ID 从新到旧，每次加载 20 条，可继续加载。
- 首页只加载词库；语境索引和帖子正文按需获取，避免一次下载、渲染全部帖子。

## 本地运行和检查

```bash
python3 -m http.server 8000 --bind 127.0.0.1
python3 -m unittest discover -s tests
node --check app.js
```

浏览器需通过 Web 服务器打开，不能直接使用 `file://`。收藏保存在当前浏览器的 localStorage 中。

## 复现导入与构建

从上述固定提交下载 `ElonMusk'sTweets.csv`，以及 `data/all_musk_posts (1).zip`，将 ZIP 内的 `all_musk_posts (1).csv` 解压到仓库外。然后从仓库根目录执行：

```bash
python3 scripts/import_archive.py "/path/to/ElonMusk'sTweets.csv" --dataset legacy
python3 scripts/import_archive.py "/path/to/all_musk_posts (1).csv" --dataset recent
python3 scripts/build_data.py
```

默认导入该文件中所有符合规则的记录；`--limit N` 可选用于诊断小样本，不能用于声称导入全档。导入只替换同来源的此前导入，保留其他来源和用户样本，并按 ID 去重。先 legacy 后 recent 可复现本版本的来源优先级。

脚本检查 CSV SHA-256，不接受意外版本：

- legacy：`16eafc4a2d9537750385319d0b396a071160feefccc879bf161999a4404bdfc0`
- recent（解压后的 CSV）：`e3a2d1cecd2f2313b3af9806144fc2d50ce8f4ca605e4006b82c266656912f54`

其他版本或新数据源应先检查字段、作者、正文边界、ID 精度、转发标记和许可，再明确更新适配及校验值。切勿将浮点数四舍五入的帖子 ID 当作原始 ID；不要绕过校验或伪造原帖。

原始标准化记录在 `data/posts.json`，词典在 `data/dictionary.json`。`build_data.py` 确定性生成：

- `data/words.json`：轻量词库、词次、关联帖数、覆盖范围与统计口径。
- `data/contexts/a.json` 等：单词对应的全部帖子 ID。
- `data/post-index.json`：帖子 ID 到正文分块文件的索引。
- `data/post-chunks/0000.json` 等：每块最多 400 条正文及来源。

修改记录或词典后运行构建，提交所有生成文件。不要手动修改生成文件。构建清理这两个生成目录内不再需要的 JSON 文件；不要在里面存放其他文件。部署 CI 会检查测试及生成文件是否一致。

## 持续扩充方向

当前已导入这两份固定存档中的全部可用记录，下一阶段重点是 **2025 年 4 月之后的缺口**，以及旧存档遗漏的内容。可接入有权限的 X API / 授权导出或其他可审计数据集；保留原始精确 ID、作者、时间、正文、转发与引用标记和来源版本，跨来源去重。自动化采集尚未配置，不会自动覆盖新增帖子、图片里的文字、视频或访谈转录。

## 部署

`.github/workflows/deploy.yml` 在 `main` 推送时测试、构建一致性检查并部署 GitHub Pages。仓库 Settings → Pages → Source 选择 GitHub Actions。环境快照发布和网站部署是不同操作；代码推送与 Actions 成功后才能确认网站发布。
