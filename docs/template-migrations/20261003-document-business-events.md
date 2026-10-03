# 业务口径与 AI 工作事件的增量采用

本能力扩展既有来源收录协议，兼容 v1 文件原文，新增 v2 业务事项/修订/工作过程和结构化工作事件入口。开发源码不等于已公开发行；不可覆盖已发布 2.9.0 制品。

| 资产 | 采用与保护规则 |
| --- | --- |
| 采集脚本、事件模板和规范 | 先对比项目自定义再语义合并；无额外服务、依赖或聊天历史读取 |
| Agent entry | 增量合并 preferred_schema、event_schema、event_template、record_action、closeout_check、automatic_triggers |
| Agent rules | 增加 capture_business_and_work_events，保留已有权限和只读边界 |
| 来源文件 | 不从源仓导入真实记录，不改旧 v1，不依据标题相似自动确认为业务事实 |
| 文档中心消费者 | 同时支持 v1/v2；业务规则按确认和修订图判定，工作记录独立投影 |
| Kit/Catalog | 由 Seed 维护者同步模板及指纹，派生项目不手工伪造锁文件 |

在临时项目验证 `preview-event`、`record-event`、重复 unchanged、`check-event` verified、只读拒绝、AI 推断确认拒绝、跨事项修订拒绝。再用当前获准的真实任务收录一个事件，并回读主仓视图。模板来源 commit 与本轮选定路径单独记录，不能把部分采用冒充完整模板升级。

自动积累依赖 Agent 遵循项目入口：长任务在里程碑收录，结束前检查回执；无写工具或用户禁记时提供待收录摘要。平台任务/人工确认仍由原主账负责，不因来源记录而更新。
