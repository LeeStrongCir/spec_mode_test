---
description: 执行创建测试计划工作流，使用计划模板构建特性测试设计方案。
handoffs: 
  - label: 创建测试任务
    agent: speckit-test.tasks
    prompt: 将测试设计方案拆分为具体任务
    send: true
  - label: 创建检查清单
    agent: speckit-test.checklist
    prompt: 为以下场景创建一个检查清单...
---

## 用户输入

```text
$ARGUMENTS
```

在继续之前，你**必须**考虑用户输入（如果不为空）。

## 概要

1. **Setup**：从仓库根目录运行 `.specify/scripts/bash/setup-plan.sh --json` 并解析 JSON，获取 `FEATURE_SPEC`, `IMPL_PLAN`, `SPECS_DIR`, `BRANCH`。对于参数中的单引号（如 "I'm Groot"），使用转义语法：`'I'\''m Groot'`（或尽可能使用双引号：`"I'm Groot"`）。

2. **加载上下文**：读取 `FEATURE_SPEC` 和 `.specify/memory/constitution.md`。加载 `IMPL_PLAN` 模板（已复制）。

3. **执行计划工作流**：遵循 `IMPL_PLAN` 模板中的结构：
   - 填写 **测试上下文**（将未知项标记为 `[NEEDS CLARIFICATION: 具体问题]`）
   - 从 **宪章** 填写 **宪章门禁** 部分
   - 评估 **门禁**（如果违反无正当理由则抛出错误）
   - 阶段 0: 生成 `research.md`（解析所有 `[NEEDS CLARIFICATION]`）
   - 设计完成后重新评估 **宪章门禁**

4. **停止并报告**：命令在 测试计划 完成后结束。报告 branch、`IMPL_PLAN` 路径和生成的 制品。

## 阶段

### 阶段 0: 大纲与研究

1. **从上述测试上下文中提取未知项**：
   - 对于每个 `NEEDS CLARIFICATION` → 研究任务
   - 对于每个 `dependency` → 最佳实践任务
   - 对于每个 `integration` → 模式任务

2. **生成并分发研究代理**：

   ```text
   针对 测试上下文 中的每一个未知项：
     任务："针对 {测试上下文}，调研 {未知项}"
   针对每一项技术选型：
     任务："在 {领域} 中，查找关于 {技术} 的最佳实践"
   ```

3. **在 `research.md` 中整合发现**，使用如下格式：
   - 决策: [选择了什么]
   - 理由: [为什么选择]
   - 考虑的替代方案: [还评估过哪些替代方案]

**输出**：所有 `NEEDS CLARIFICATION` 已解决的 `research.md`

## 核心规则

- 对文件系统操作使用 **绝对路径**；对文档和代理上下文文件中的引用使用 **项目相对路径**
- 如果门禁失败或 `NEEDS CLARIFICATION` 未解决，则抛出错误
