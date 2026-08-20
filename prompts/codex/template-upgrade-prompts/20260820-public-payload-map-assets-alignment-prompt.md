# 派生项目升级提示词：公开 payload 地图资产对齐

```text
请在当前派生项目会话中完成“公开 payload 模块地图与技术地图资产对齐”升级，不要只生成给另一个会话的提示词。

模板来源通道：public_seed
公开模板仓库：https://github.com/mawflow/mawflow-seed
目标版本：v2.3.2
迁移说明：docs/template-migrations/20260820-public-payload-map-assets-alignment.md

要求：
1. 先审计目标项目事实，只做增量语义合并；不得覆盖 README、code、app_key、发布配置、仓库映射、secrets、.local、模块档案、已有能力/信号或 WIP。
2. 缺少 .maw/module-candidates.yaml、.maw/capabilities.yaml、.maw/project-signals.yaml 时，从 v2.3.2 公开空索引初始化；已有文件只补缺失 schema/registry 字段，保留项目条目。
3. 同步 docs/changelogs、docs/technical-map、能力/信号模板和公开可运行脚本；公共文档不得引用目标项目不存在的必需命令。
4. 先运行 migrate-module-changelogs.py plan；只有计划无冲突时才 migrate --execute，随后 check，重复执行必须零额外变化。
5. 在当前项目运行 check-template-module-docs.sh、check-module-candidates.sh、check-technical-map.sh 和 extract-project-metadata.py；缺少可选仓库身份、TODO 或经验索引时应返回兼容结果。
6. 更新 .maw/template-source.yaml 的 applied_version 为 v2.3.2 对应公开 commit，完成验证、提交、推送，并按有效 mirror 计划决定是否同步。
```
