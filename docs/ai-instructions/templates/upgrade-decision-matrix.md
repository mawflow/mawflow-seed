# 升级取舍矩阵模板

| 项 | 源模板参考 | 目标项目现状 | 风险等级 | 决策 | 处理方式 | 保护边界 | 验证 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  | R0/R1/R2/R3/R4 或 T0/T1/T2/T3/T4 | adopt / adapt / skip / manual_confirm |  | README、code、.local、secrets、repositories、releases、app_key、模块档案 |  |  |

## 决策含义

- `adopt`：目标项目缺失且风险可控，按源模板新增。
- `adapt`：目标项目已有同类能力，只做语义合并。
- `skip`：不适用于目标项目或仅为源模板内部说明。
- `manual_confirm`：涉及高风险边界，等待人工确认后再执行。

## 保护边界

升级矩阵必须显式保护：

- 目标项目 README 和业务说明。
- `code/` 业务源码、业务运行配置和 app_key。
- `.local/` 本机资料和真实配置。
- secrets、repositories、releases、客户仓库映射和镜像目标。
- 现有模块档案、changelog、项目私有规则和发布流程。
