# Prompt Pack 示例

## name

feature-brief-to-task

## purpose

把一句功能想法整理成 AI 可执行任务。

## prompt_spec

```text
目标：实现 <功能>。
背景：当前项目已有 <事实>。
允许修改：<路径>。
禁止修改：.local/**、真实 secret、无关组件。
验收：<用户行为>、<测试命令>、<文档更新>。
收口：说明变更、验证、风险和发布影响。
```

## sanitization

公开前删除真实项目名、客户名、账号、URL、token 和日志。
