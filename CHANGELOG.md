# 修改日志

项目的重要变更记录在此文件中。

## [未发布]

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

### 修复

- 修复 Gitee Go 在 detached HEAD 状态下执行 `git push` 失败的问题，改为显式推送 `HEAD:main`。
- 将依赖安装、搜刮和提交合并在同一个 Gitee Go step 中，避免跨 stage 丢失 Python 依赖。
- 修正 Gitee Go 流水线文件名和 Python 命令，使 `.workflow/master-pipeline.yml` 可被识别和执行。

### 新增

- 新增 Gitee Go 自动搜刮流水线，与 GitHub Actions 保持相同的核心搜刮流程。
