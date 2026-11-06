# MuskWords — 从 Elon Musk 真实帖子学习英语

[目标网站](https://sukaidie.github.io/muskwords/) · 静态网页，无 API 密钥、无需服务器。

## 当前状态 / 数据真实性

**当前只包含 2026-11-06 的 6 条逐条核对的真实帖子（4 条原创 + 2 条回复），不是全部历史。** 数据来自 [Elon Musk Archive](https://www.elonmuskarchive.org/)，每条记录都有独立存档及 X 链接。词频完全根据当前 `data/posts.json` 计算，**绝不外推到所有推文**。中文释义是学习辅助，非词典正式授权内容。第三方存档并非 X 官方数据；全部历史及完整性未验证。

## 已实现

- 中文释义、英文发音（浏览器 TTS）、CEFR 等级（人工标注）、真实词频、帖子出处
- 关键词/中文搜索、按等级筛选、频率/字母排序
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
{"id":"数字形式的真实帖子 ID","date":"YYYY-MM-DD","type":"original 或 reply","text":"马斯克本人写的文本，不含别人的引用内容","source":"https://可核查的来源","url":"https://x.com/elonmusk/status/真实ID","verified":true}
```

不得把第三方转发内容作为马斯克本人发言，`type=retweet` 被处理脚本自动排除。添加词语中文释义到 `data/dictionary.json` 后执行：

```bash
python3 scripts/build_data.py
```

把 `data/posts.json`、`data/dictionary.json`、`data/words.json` 一起提交，网站就更新了。没有翻译的词显示“释义待核实”，不会编造意思。不要通过客户端访问需保密的 X API token。

### 大规模历史数据

要真正接近全部发言，需合法获取 X API 历史数据或经授权的数据导出；X 访问有权限、速率和费用限制。当前仓库**没有自动抓取全部历史的功能**。大量逐条内容转载前请核查 X 和第三方数据源的使用许可。建议定期使用合法导出的数据按本结构导入，并在 metadata 中标注实际年份和覆盖范围。`scripts/build_data.py` 的 `lastBuilt` 和 `coverage` 当前为固定的已核实种子数据日期；后续扩充时需同步修改，不能沿用原有声明。

## 技术栈

原生 HTML / CSS / JavaScript + Python 3 标准库，GitHub Pages。无第三方 npm 依赖。
