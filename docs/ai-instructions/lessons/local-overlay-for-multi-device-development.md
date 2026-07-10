# 多设备 `.local` overlay 经验

## 适用场景

多台开发设备、AI 节点、本机调试环境或模板仓库维护者共享同一个项目仓库时。

## 经验

`.local/` 是当前设备差异层，不是项目共享事实来源。真实本机路径、端口、代理、工具链、浏览器调试 profile、SSH key 路径和维护者临时记录都应留在 `.local/`，并被 git 忽略。

项目共享记忆应进入 `docs/ai-instructions/`，例如用户澄清、长期偏好、项目术语、执行经验和可复用流程。本机临时状态可以进入 `.local/ai/` 或 `.local/ai-runs/`。

## 实践

- 只提交 `.local/**/README.md` 和 `.local/**/*.example.yaml`。
- 真实设备配置从 `.local/device.example.yaml` 复制到本机私有文件后填写。
- 需要脚本读取的本机覆盖使用 `.local/<same-path>`，例如 `.local/.maw/repositories.yaml`。
- 外部交付、客户仓库同步和脱敏检查使用 no-local 选项，避免带入本机差异。

## 验证

- `ops/scripts/check-local-boundary.sh`
- `ops/scripts/check-ai-memory-consistency.sh`
