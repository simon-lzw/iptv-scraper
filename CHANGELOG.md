# 修改日志

项目的重要变更记录在此文件中。

## [未发布]

### 修复

- 修复 Gitee Go 在 detached HEAD 状态下执行 `git push` 失败的问题，改为显式推送 `HEAD:main`。
- 将依赖安装、搜刮和提交合并在同一个 Gitee Go step 中，避免跨 stage 丢失 Python 依赖。
- 修正 Gitee Go 流水线文件名和 Python 命令，使 `.workflow/master-pipeline.yml` 可被识别和执行。

### 新增

- 新增 Gitee Go 自动搜刮流水线，与 GitHub Actions 保持相同的核心搜刮流程。
