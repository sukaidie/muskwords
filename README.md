# MuskWords — 从 Elon Musk 真实帖子学习英语

[目标网站](https://sukaidie.github.io/muskwords/) · 静态网页，无 API 密钥、无需服务器。

## 当前状态 / 数据真实性

**当前收录 206 条来源可追溯的样本，包含 1,331 个不同词形、3,492 个词次，不是全部历史词库。**

- 原 ZIP 提供 2026-11-06 的 6 条样本及 Elon Musk Archive / X 链接。本项目未独立确认其核验声明，标记为 `provided_sample`。
- 新增 200 条历史存档记录，时间为 2022-05-20 至 2022-06-03，来自 [MohrezSheikh/Elon-Musk-Tweets](https://github.com/MohrezSheikh/Elon-Musk-Tweets/tree/18bee13cf1acb251087343221478bf76ab45ee1a)。按 CSV 原顺序选取前 200 条：排除 `RT @` 开头的纯转发，以及去掉链接、提及后不足 4 个英文片段的记录。不是随机抽样，也不是连续日期的完整覆盖。每条记录保存原帖 ID、X 链接、固定版本 CSV 来源和零起始 `archiveRow`。以 `@` 开头推断为回复，其他记录标记为原创；CSV 不含官方对话元数据，分类可能存在误差。
- 历史记录已与上述 CSV 对照，**尚未逐条与 X 原帖核对**。标记为 `archive_record`、`verified: false`，不会将第三方存档冒充官方验证结果。第三方数据集的许可证见 [data/ARCHIVE-LICENSE.txt](data/ARCHIVE-LICENSE.txt)，上游许可不代表取得全部帖子文字的独立授权。
- 词频由当前 `data/posts.json` 复算，保留表层词形，不外推到全部帖子。网页显示非连续选样范围和数据边界。
- 当前 739 个词有中文释义及人工参考等级，592 个词仍显示“释义待核实 / 未标注”。CEFR 是人工估计的学习参考，并非官方或词典认证；未标注词、专有名词不会混入“B1 及以上”等范围。

## 已实现

- 中文释义、英文发音（浏览器 TTS）、CEFR 等级（人工参考）、样本词频、帖子出处
- 关键词/中文搜索、按最低等级（如 B1 及以上、C1 及以上）或单一等级筛选、频率/字母排序
- 本地生词收藏、筛选结果导出 CSV、移动端自适应
- 排除纯转发、帖子按 ID 去重、词频可通过 Python 复算
- GitHub Actions 自动部署到 GitHub Pages

## 发布到 GitHub Pages

1. 在 GitHub 新建 **Public** 仓库 `sukaidie/muskwords`，不要初始化 README。
2. 将本项目文件（含隐藏的 `.github/workflows/deploy.yml`）上传到 `main`。可以通过 Git 命令：

```bash
unzip muskwords.zip -d muskwords
cd muskwords
 git init
 git add .
 git commit -m "Initial MuskWords verified-data MVP"
 git branch -M main
 git remote add origin https://github.com/sukaidie/muskwords.git
 git push -u origin main
```

3. 到 **Settings → Pages → Build and deployment → Source** 选择 **GitHub Actions**。
4. 在 **Actions** 标签检查 `Deploy MuskWords to GitHub Pages` 是否成功，成功后网站在 `https://sukaidie.github.io/muskwords/`。

## 新增真实帖子

编辑 `data/posts.json`，每条包含：

```json
{"id":"数字形式的真实帖子 ID","date":"YYYY-MM-DD","type":"original 或 reply","text":"马斯克本人写的文本，不含别人的引用内容","source":"https://可核查的来源","url":"https://x.com/elonmusk/status/真实ID","sourceStatus":"archive_record","verified":false}
```

不得把第三方转发内容作为马斯克本人发言，`type=retweet` 被处理脚本自动排除。先核对记录来源并选择 `sourceStatus`：`archive_record` 表示与第三方存档对照，`provided_sample` 表示用户提供的记录，均不意味着官方核验。没有来源状态且 `verified` 非 true 的记录不会计入。

添加词语中文释义到 `data/dictionary.json` 后执行：

```bash
python3 scripts/build_data.py
```

把 `data/posts.json`、`data/dictionary.json`、`data/words.json` 一起提交，网站就更新了。没有翻译的词显示“释义待核实”，不会编造意思。不要通过客户端访问需保密的 X API token。

### 大规模历史数据

要真正接近全部发言，需合法获取 X API 历史数据或经授权的数据导出；X 访问有权限、速率和费用限制。当前仓库**没有自动抓取全部历史的功能**。大量逐条内容转载前请核查 X 和第三方数据源的使用许可。建议定期使用合法导出的数据按本结构导入，并在 metadata 中标注实际年份和覆盖范围。`coverage` 自动从实际收录日期计算，并标明非连续选样；`lastBuilt` 当前为本版构建日期，后续发布时应更新。

## 技术栈

原生 HTML / CSS / JavaScript + Python 3 标准库，GitHub Pages。无第三方 npm 依赖。

## 复现历史样本导入

下载上述固定提交的 `ElonMusk'sTweets.csv`（无需密钥），然后执行：

```bash
python3 scripts/import_archive.py "/path/to/ElonMusk'sTweets.csv" --limit 200
python3 scripts/build_data.py
```

导入脚本检查 SHA-256：`16eafc4a2d9537750385319d0b396a071160feefccc879bf161999a4404bdfc0`。它只替换同一数据集版本的既有导入，保留其他样本，重复执行不产生重复记录。使用其他版本前，应核查来源和许可并明确更新版本与校验值，不要绕过校验。提高 limit 后会产生更多未标注词，需同步补充词典。

## 本地运行和验证

```bash
python3 -m http.server 8000 --bind 127.0.0.1
python3 -m unittest discover -s tests
node --check app.js
```

筛选范围遵循 A1 < A2 < B1 < B2 < C1 < C2。例如“B1 及以上”包括 B1、B2、C1、C2；“C1 及以上”包括 C1、C2。“仅 B1”仍只显示 B1。搜索、收藏、排序与 CSV 导出都使用当前筛选结果。当前暂无 C2 标注词，选择相应范围会显示空结果。
