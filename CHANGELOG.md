# 修改日志

项目的重要变更记录在此文件中。

## [未发布]

### Bug 修复

- **`db.py`**：
  - 修复 `add_channel()` 参数数量不匹配（11 个占位符缺 `kodi_props` 值）导致必崩的 `ProgrammingError`
  - 修复连接泄漏：`_get_conn()` 改为上下文管理器（自动 commit + close）
  - `_row_to_channel()` 补读 `kodi_props` 字段（此前从 DB 读出的 DRM 频道信息恒为空）
  - `get_channel_by_name()` LIKE 查询转义 `%`/`_` 通配符
  - 新增 `channel_exists(name, url)` 索引查询方法
- **`output_generator.py`**：M3U 输出过滤失效频道（`is_active=False`），修复验证后死链仍输出的问题；删除未使用的 `group_by_country` 参数；`countries.json` 统计排除未知国家（与 all.m3u 一致）
- **`pipeline/orchestrator.py`**：多源合并移到验证/评分**之后**，主源按真实评分选择（可用且评分最高），失效源自动降级；删除未使用导入
- **`checker.py`**：`HealthChecker.__init__` 补 `self.logger`，修复 `deep_check_inactive()` 必崩的 `AttributeError`
- **`scrapers/base.py`**：删除无效的 `session.timeout = 15` 赋值；`_classify_region` 与 `main.py` 统一使用 `GROUP_REGION_MAP` 单一数据源（按关键词长度降序匹配，长词优先），并补齐繁体/变体关键词（有線/澳視/台視/jade/pearl/凤凰卫视/澳门卫视/香港卫视等）
- **`main.py`**：`_classify_region` 补排除逻辑（杭州明珠/六鳌翡翠湾）；`_count_new_channels` 改为逐条索引查询，避免全表加载
- **`m3u_generator.py`**：频道名/分组/tvg-id/logo 转义引号、反斜杠和换行，防止破坏 M3U 格式
- **`pipeline/ranker.py` / `pipeline/validator.py`**：删除死代码（`pick_best`、`_HLS_MARKERS`、`_SEGMENT_RE`）

### 新功能：全球 IPTV 管线

- **全球频道覆盖**：新增 `countries.py` 国家/地区映射表（130+ 国家，ISO 3166-1 alpha-2），
  支持国家代码/英文名/中文名/大区统一管理。
- **模块化处理管线**：新增 `pipeline/` 包：
  - `normalizer.py` - 频道名/分组标准化
  - `deduplicator.py` - URL 去重 + 同频道多源合并（含 token 参数处理）
  - `classifier.py` - 国家/地区自动分类（group/频道名/URL 域名/TLD 综合判断）
  - `ip_detector.py` - IPv4/IPv6 协议识别 + 域名解析
  - `validator.py` - HLS 直播源有效性验证（检查 playlist 分片）
  - `speed_tester.py` - 下载速度/首字节延迟/稳定性测速
  - `ranker.py` - 综合质量评分（可用性+IPv4+响应+速度+稳定性+国内访问，权重可配置）
  - `orchestrator.py` - 管线编排器（采集→标准化→分类→去重→验证→评分→排序）
- **多层级输出**：新增 `output_generator.py`，生成：
  - `output/all.m3u` - 全球总频道
  - `output/Greater-China.m3u` - 中国大陆/香港/澳门/台湾汇总
  - `output/countries/XX.m3u` - 各国家/地区独立文件
  - `output/metadata/countries.json` + `channels.json` - 元数据
- **IPv4 优先**：`IP_TYPE_PREFER=ipv4` 配置，IPv4 直连 > 双栈 > 域名 > 仅 IPv6
- **国内网络优化**：`GITHUB_RAW_PROXY` 支持 ghproxy 代理前缀加速 raw 源访问
- **配置可调**：`SCORE_WEIGHTS`、`ENABLE_SPEED_TEST`、`MIN_SPEED_KBPS`、
  `ENABLE_STREAM_VALIDATION`、`MAX_CONCURRENT_CHECKS` 均可配置
- **新数据源**：新增 iptv-org（JP/KR/US/GB/SG/MY）、Free-TV/IPTV、iptv-org all streams
- **CLI 入口**：`python main.py --global-pipeline` 运行全球管线；
  `--no-validate` 跳过流验证
- **参考调研**：`docs/RESEARCH.md` 记录 10 个开源 IPTV 项目调研成果；
  `docs/ARCHITECTURE.md` 记录模块化架构设计

### 文档

- 更新 README 快速开始方式 A/B：补充 `playlist_cn.m3u`、`playlist_ipv4.m3u`、`countries/XX.m3u` 等全球播放列表链接，国内推荐 IPv4 优先列表。
- 更新 README 本地运行：补充 `--global-pipeline` / `--no-validate` 运行选项及 `output/` 目录输出说明。
- 更新 README 数据流图：补充全球管线分支（分类 → IPv4 检测 → 验证 → 测速 → 评分 → 多层级输出）。

### 修复

- 修复 Gitee Go 在 detached HEAD 状态下执行 `git push` 失败的问题，改为显式推送 `HEAD:main`。
- 将依赖安装、搜刮和提交合并在同一个 Gitee Go step 中，避免跨 stage 丢失 Python 依赖。
- 修正 Gitee Go 流水线文件名和 Python 命令，使 `.workflow/master-pipeline.yml` 可被识别和执行。

### 新增

- 新增 Gitee Go 自动搜刮流水线，与 GitHub Actions 保持相同的核心搜刮流程。
