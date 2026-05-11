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
   - 填写测试上下文（将未知项标记为 "NEEDS CLARIFICATION"）
   - 从 constitution 填写 Constitution Check 部分
   - 评估 gates（如果违反无正当理由则 ERROR）
   - Phase 0: 生成 `research.md`（解析所有 NEEDS CLARIFICATION）
   - 设计完成后重新评估 Constitution Check

4. **停止并报告**：命令在 planning 完成后结束。报告 branch、`IMPL_PLAN` 路径和生成的 artifacts。

## Phases

### Phase 0: 大纲与研究

1. **从上述 Technical Context 中提取未知项**：
   - 对于每个 NEEDS CLARIFICATION → research task
   - 对于每个 dependency → best practices task
   - 对于每个 integration → patterns task

2. **生成并分发 research agents**：

   ```text
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **在 `research.md` 中整合发现**，使用如下格式：
   - Decision: [选择了什么]
   - Rationale: [为什么选择]
   - Alternatives considered: [还评估过哪些替代方案]

**输出**：`research.md` 且所有 NEEDS CLARIFICATION 已解析

## 核心规则

- 对文件系统操作使用 absolute paths；对文档和 agent context 文件中的引用使用 project-relative paths
- 如果 gates 失败或 clarifications 未解决，则 ERROR
