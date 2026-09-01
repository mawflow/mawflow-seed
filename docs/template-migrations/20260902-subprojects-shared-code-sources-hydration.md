# 多子项目、共享代码源与新设备补全

- 日期：2026-09-02
- 风险等级：T3
- 源模板基线：`1dffca46b69b33ee3aa8113744448612db7dc893`（v2.4.0）
- 适用范围：一个 MAWflow 项目内维护多个客户、部署组或其它独立子项目，以及使用独立 Git 目录的派生项目。

## 新模型

- `.maw/subprojects.yaml` 是项目内独立交付单元清单。组件通过 `subproject_ref` 归属子项目，但仍独立拥有 app_key、构建、运行、发布和回滚记录。
- `.maw/code-sources.yaml` 是共享代码源注册表。同一 Git 仓库只登记一次，多个组件通过 `source.repository_ref` 与 `repository_subpath` 使用同一工作副本。
- `.local/.maw/code-source-bindings.yaml` 只保存当前设备的绝对目录和 Git Access Profile 引用。托管 clone 默认放在 `.local/code-sources/<source-key>/`。
- `.maw/releases.yaml` 的 `releases.groups` 只做非原子协调顺序；组件发布仍可单独选择、审批和回滚。

## 为何允许项目内嵌套 Git

原“托管 clone 不得位于项目根目录内”的目标是防止独立仓库进入外层 Git，而不是限制文件系统位置。2.5 将安全条件改为：只要目标位于项目根目录内，就必须能由外层 Git 确认已被忽略；默认并推荐使用 `.local/code-sources/`，模板通过 `/.local/code-sources/**` 明确忽略。这样新设备路径稳定、项目可搬迁，同时不会形成外层仓库可追踪的嵌套 Git。

## 既有项目取舍矩阵

| 目标项目状态 | 处理 |
| --- | --- |
| 没有子项目配置 | 新增 `default`；没有 `subproject_ref` 的组件按 `default` 解析 |
| 已有自己的项目分组 | 映射为稳定 subproject key，保留 app_key 和现有发布配置 |
| 2.4 组件级外部 Git | 保持原声明和本机绑定可用，不强制转换 |
| 多组件指向同一仓库且绑定同一 Git 根 | 用显式归并计划创建一个 code source，复用目录，不移动源码 |
| 同仓库组件绑定到多个不同 Git 根 | fail closed，由人工选择保留哪个工作副本后再归并 |
| 新设备缺少独立 Git 目录 | 运行 `mawflow project hydrate`，默认 clone 到 `.local/code-sources/<source-key>/` |
| 自定义 clone 目录 | 显式绑定已有 Git 根；仍只写入本机配置 |
| 需要同服协调发布 | 配置非原子 release group；保留组件级选择、审批、状态和回滚 |

## 云端边界

云端可以同步 source key、关联组件和 `binding_required` readiness。禁止同步本机绝对路径、Git Access Profile、凭据、源码内容、HEAD/dirty 详情、分支工作区和未提交改动；跨设备开发仍由各 Git 仓库远端承担源码同步。

## 验证

```bash
git diff --check
python3 -m pytest -q tests/test_seed_kit_v2.py
mawflow project doctor --root .
git check-ignore .local/code-sources/example/README.md
```

升级与归并都必须预览、精确确认并保留私有回滚备份；任何操作不得移动或删除已有源码目录。
