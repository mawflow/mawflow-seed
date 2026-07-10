# 执行经验候选台账

本文件用于暂存 AI/Codex 在执行任务过程中通过试错得到的可复用经验。典型场景是：先用了错误方法、错误命令、错误运行时或错误路径，失败后定位到正确方法；这类信息应记录下来，避免后续会话重复踩坑。

当某条执行经验多次适用、风险较高或已经形成稳定判断时，应升级为：

- `docs/ai-instructions/lessons/<topic>.md`：复盘经验、踩坑记录、固定处理方式。
- `docs/ai-instructions/solutions/<category>/<topic>.md`：较大的具体解决方案、完整排查过程、命令序列和验收清单。
- `docs/ai-instructions/instructions/<topic>.md`：可执行流程或检查清单。
- `docs/ai-coding/` 或组件 guide：如果它直接影响编码、测试、构建或发布规则。

## 使用规则

- AI 执行命令失败后，自己找到正确命令、正确版本、正确路径或正确配置来源时，应记录。
- 同类错误在多个任务中可能重复出现时，应记录。
- 收口验证阶段发现“默认命令不对、运行时版本不对、脚本入口不对、测试目录不对、浏览器策略不对”等，应记录。
- 只记录可复用的经验，不记录无意义的偶发网络抖动或一次性误输入。
- 不记录真实密钥、token、账号密码、客户隐私、生产连接串或不可外传资料。

## 候选表

| 标题 | 关键词 | 首次记录 | 最近更新 | 错误尝试/症状 | 正确方法 | 触发场景 | 验证方式 | 相关 module_key | 相关路径/命令 | 状态 | 升级目标 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `rtk read` 不适合一次传多个文件 | rtk read、多文件读取、启动上下文 | 2026-06-14 | 2026-06-14 | 执行 `rtk read README.md TEMPLATE_OVERVIEW.md ...` 时触发 shell `read` 行为并失败。 | 对多个文件使用逐文件 `rtk read`，或仅在需要机器精确输出时使用限定范围的 `rtk proxy sed -n`。 | 读取任务包启动上下文、仓库规则、多个 README。 | 逐文件读取成功。 | not_identified | `rtk read`, `rtk proxy sed -n` | candidate |  |
| `rtk find` 不支持复杂谓词 | rtk find、compound predicates、文件定位 | 2026-06-14 | 2026-06-14 | 使用 `rtk find ... \\( -name ... -o ... \\)` 时失败，提示不支持 compound predicates/actions。 | 用简单 `rtk find <dir> -maxdepth ... -type f` 后再按需 `rtk grep`，或使用限定范围的 `rtk proxy find`。 | 查询目标文件是否存在、定位新增文档。 | 简单 find/grep 后继续执行成功。 | not_identified | `rtk find`, `rtk proxy find` | candidate |  |
| 总模板检查会因 `.DS_Store` 失败 | .DS_Store、check-template-module-docs、生成物清理 | 2026-06-14 | 2026-06-14 | `rtk bash ops/scripts/check-template-module-docs.sh` 因 `docs/.DS_Store` 和 `prompts/.DS_Store` 失败。 | 删除 `.DS_Store` 生成物并重跑总模板检查。 | 模板文档检查、提交前验证。 | 清理后 `rtk bash ops/scripts/check-template-module-docs.sh` 通过。 | not_identified | `ops/scripts/check-template-module-docs.sh`, `find . -name .DS_Store` | candidate |  |
|  |  |  |  |  |  |  |  |  |  | candidate |  |

当某条执行经验需要承载完整解决方案时，不要把正文塞进本表；应在本表保留摘要和关键词，在 `experience-index.md` 登记 `EXP-XXX`，并把详细方案写入 `solutions/**`。

状态建议：

- `candidate`：已暂存，有复用价值但尚未稳定。
- `refining`：多次出现或正在补充触发条件。
- `lesson_created`：已升级为正式经验文档。
- `solution_created`：已升级为解决方案详情文档。
- `instruction_created`：已升级为正式指令。
- `coding_rule_created`：已同步到 `docs/ai-coding/` 或组件 guide。
- `merged`：已合并到其它条目。
- `ignored`：确认无需继续跟踪。

## 记录示例

- 标题：收口测试必须使用项目指定 Python。
- 关键词：python 版本、测试命令、收口验证。
- 错误尝试/症状：使用系统默认 `python` 或错误虚拟环境运行测试失败。
- 正确方法：先读取项目 README、组件 guide 或锁定文件，使用指定 `python3.x`、虚拟环境或工具链命令。
- 触发场景：测试、构建、脚本验证、文档渲染等收口阶段。
- 验证方式：记录最终成功命令和必要的版本检查命令。

## 升级规则

- 同一执行错误出现两次以上，优先升级为正式 lesson；如果解决步骤较长或需要完整排查过程，升级为 solution 并同步 `experience-index.md`。
- 如果正确方法是强制流程，升级为 instruction。
- 如果正确方法直接约束编码、测试、构建或发布，补充到 `docs/ai-coding/`、组件 guide 或相关脚本 README。
