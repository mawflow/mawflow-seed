# 组件工程说明

本目录按实际组件维护工程结构、命令、边界和常见改动入口。

新种子不内置组件 guide。通过 `mawflow component init/adopt` 建立组件后，可按项目复杂度补充 `<component>.md`，并与 `code/<component>/.maw.component.yaml` 保持一致。

组件 guide 只描述端工程边界，不替代业务模块档案。业务模块应继续在 `docs/modules/` 中按 group / leaf 拆分。

不要预设 `server`、`client`、管理后台或移动端；组件名称和类型以项目事实为准。
