# GitHub 开发流程

本文档定义 `embedded-platform-core` 的日常 GitHub 协作流程。目标是让 `main`
始终保持可构建、可测试、可发布，所有功能通过独立分支、Pull Request、CI
和代码审查进入主干。

## 分支角色

`main` 是受保护主干，只保存已经通过自动化测试和审查的代码。开发者不要直接在
`main` 上提交功能、修复或实验代码。

功能开发、问题修复、工程维护和文档修改都应该从最新 `main` 拉出短生命周期分支：

```bash
git checkout main
git pull --ff-only origin main
git checkout -b feature/linux-osal-time
```

推荐分支命名：

- `feature/<name>`：新增功能或模块
- `fix/<name>`：缺陷修复
- `test/<name>`：测试补充
- `docs/<name>`：文档修改
- `chore/<name>`：工程维护、目录、模板、流程调整
- `ci/<name>`：GitHub Actions 或其他 CI 配置修改

## 日常开发步骤

1. 从最新 `main` 创建工作分支。
2. 在工作分支上完成一个边界清晰的变更。
3. 本地运行测试和构建。
4. 提交代码并推送分支。
5. 在 GitHub 创建 Pull Request。
6. 等待 CI 通过并完成代码审查。
7. 使用 `Squash and merge` 合并回 `main`。
8. 删除已经合并的远端和本地功能分支。

本地验证命令：

```bash
pytest tests/host_unit tests/api_contract -v
cmake -S . -B build
cmake --build build
```

提交前建议检查：

```bash
git status
git diff
git add .
git diff --cached
git commit -m "feat: implement linux osal time"
```

提交信息使用 Conventional Commits 风格：

- `feat:` 新功能
- `fix:` 缺陷修复
- `test:` 测试
- `docs:` 文档
- `build:` 构建系统
- `ci:` CI 配置
- `chore:` 工程维护
- `refactor:` 不改变行为的重构

## Pull Request 要求

每个 Pull Request 应该只解决一个明确问题。不要把无关重构、格式化、功能开发和
文档修改混在一个 PR 里。

PR 描述至少包含：

```markdown
## Summary

- 本次变更做了什么
- 涉及哪些模块或接口

## Validation

- [ ] pytest tests/host_unit tests/api_contract -v
- [ ] cmake -S . -B build
- [ ] cmake --build build
```

如果 PR 修改公共 API、OSAL/HAL 接口、平台适配层或启动流程，必须说明兼容性影响。

## CI 检查

GitHub Actions 会在 push 和 Pull Request 时运行 CI。当前最低要求是：

```bash
pytest tests/host_unit tests/api_contract -v
cmake -S . -B build
cmake --build build
```

CI 失败时，不要合并 PR。开发者应该在原分支修复问题并再次 push，PR 会自动更新。

## main 保护规则

GitHub 仓库建议为 `main` 配置分支保护：

- Require a pull request before merging
- Require approvals: 1
- Require status checks to pass before merging
- Require branches to be up to date before merging
- Do not allow force pushes
- Do not allow deletions

这样可以保证所有进入主干的代码都经过 Pull Request、CI 和审查。

## 合并后清理

PR 合并后，本地同步主干并删除已完成分支：

```bash
git checkout main
git pull --ff-only origin main
git branch -d feature/linux-osal-time
git push origin --delete feature/linux-osal-time
```

如果本地分支还没有被 Git 识别为已合并，先确认 GitHub PR 已经合并，再决定是否删除。
