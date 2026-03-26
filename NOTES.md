# NOTES.md — Research Notebook

## Project Info
- **Repository**: `openclaw/openclaw`
- **Corpus**: 22,613 GitHub issues (open + closed, PRs excluded)
- **Export date**: 2026-03-25
- **Data files**: `openclaw_issues.jsonl` (109MB), `openclaw_issues.csv` (103MB)
- **Crawler**: `fetch_issues.py` (3-pass strategy: asc + desc + Search API gap fill)

---

## 2026-03-25: Analysis Phase Begins

### Initial Hypotheses
1. The issue corpus likely reflects community-observed pain points rather than systematic evaluation.
2. As the project matures, issues may shift from setup/infra to deeper capability concerns.
3. Stability-related concerns (crashes, regressions, memory drift) are likely dominant.
4. Plasticity and generalization may be harder to identify from issue text alone.
5. Recurring unresolved issues may reveal persistent design tensions.

### First Impressions (pre-loading)
- 22,613 issues is a very large corpus for a single open-source project — suggests high community activity.
- Mix of open/closed will be informative for resolution patterns.
- The `labels` field should give a strong starting signal for theme categorization.
- `statement_text = title + body` is the main analysis target.

---

## Previous Notes: Data Export Phase

## 项目信息 (Export)
- **目标仓库**: `openclaw/openclaw`
- **脚本**: `fetch_issues.py`
- **输出**: `openclaw_issues.jsonl` + `openclaw_issues.csv`

---

## 问题 1：未设置 Token 导致 API 速率限制 (403)

**现象**:  
未设置 `GITHUB_TOKEN` 运行脚本，GitHub REST API 匿名限速为 60 次/小时。  
抓了 51 页后触发 `HTTP Error 403: rate limit exceeded`。

**解决方案**:  
1. 在 `.env` 文件中配置 `GITHUB_TOKEN=github_pat_xxx...`（脚本会自动读取）。  
2. 或设置环境变量: `export GITHUB_TOKEN=xxx`  
3. 认证后限速提升到 **5000 次/小时**，足以一次性抓完所有页面。

---

## 问题 2：进度文件过大导致 VS Code 崩溃

**现象**:  
初始版本将所有已抓取的 issue 数据保存在 `_fetch_progress.json` 中作为断点续传。  
8414 条 issue 后该文件达到 **44MB**，VS Code 打开/索引时频繁崩溃。

**根本原因**:  
VS Code 的文件监视器会对工作区中的 JSON 文件进行索引和语法高亮，  
大文件（>10MB）会导致编辑器卡死或内存溢出。

**解决方案**:  
1. **进度文件缩到最小**: `_progress.txt` 只存一个页码数字（几字节）。  
2. **数据增量写入 JSONL**: 每抓完一页就 append 到 `openclaw_issues.jsonl`，内存中不存历史数据。  
3. **VS Code 设置**（可选，防止大文件被索引）:  
   在 `.vscode/settings.json` 中添加：
   ```json
   {
     "files.watcherExclude": {
       "**/openclaw_issues.*": true
     },
     "search.exclude": {
       "**/openclaw_issues.*": true
     }
   }
   ```
4. 查看大 JSONL 文件建议用命令行工具: `head -5 openclaw_issues.jsonl` 或 `wc -l openclaw_issues.jsonl`。

---

## 问题 3：issues API 包含 Pull Requests

**现象**:  
GitHub REST API 的 `/repos/{owner}/{repo}/issues` 端点会同时返回 issues 和 PRs。

**解决方案**:  
在代码中过滤: 如果 item 含有 `"pull_request"` 字段，则跳过。  
每页 100 条记录中 issues 通常只占 40-60 条，其余为 PR。

---

## 架构总结

```
fetch_issues.py
├── .env                  # Token (不入 git)
├── _progress.txt         # 断点页码 (3 bytes)
├── openclaw_issues.jsonl # 增量写入的数据
└── openclaw_issues.csv   # 最终一次性生成
```

**关键设计**:
- 每页抓完 → append JSONL → 更新页码 → 即使中断也不丢数据
- 抓完全部后才生成 CSV（从 JSONL 转换）
- Token 优先读环境变量，其次读 `.env` 文件
- 遇到 403 限速时，读取 `X-RateLimit-Reset` 头精确等待（不盲目重试）
