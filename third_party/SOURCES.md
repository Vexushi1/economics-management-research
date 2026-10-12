# SOURCES.md — 第三方资源来源、固定版本与采用范围审计

> Phase 0B / 文档审计；日期：2026-10-12；目标仓库：`Vexushi1/economics-management-research`。  
> 本文件记录**上游来源的只读核查**，并非已安装、克隆、复用或运行的证明。参考基准：仓库 `MODIFICATION_PLAN.md`（Reviewed Draft v0.3，审计开始时 HEAD `2b29a45ef1cf21df750f5c473c861dfd5c7a7ab0`）。  
> 此文件及相关三份审计文件创建于 Phase 0B，不构成 Phase 1、脚本执行或版权再发布授权。

## 1. 审计方法与证据等级

- **V1 — 源代码/文件已读**：通过 GitHub Contents / Git Tree / 文件读取接口核对路径、内容、版本；不能推断运行正确或安全。
- **V2 — 上游自述**：README、SKILL frontmatter 或仓库说明的声明，尚无独立运行验证。
- **V3 — 推定/待核实**：兼容性、目标宿主、外部模型可用性、实际再分发授权不确定；统一标记 `[需要进一步确认]`。
- **状态**：`ADOPT_REFERENCE`（采用思想/规范）、`ADAPT_AFTER_REVIEW`（可能适配代码，需许可证和测试）、`REFERENCE_ONLY`（只参考）、`DEFER`（推迟）、`BLOCK_COPY`（当前不能直接复制）。以上不是代码中的已实现枚举。
- **固定版本**：以下都是 2026-10-12 GitHub 只读核查的 HEAD SHA，而不是正式版本号或 Tag；实施阶段应以 SHA 下载、核实文件散列，不能追踪浮动 `main`/`master`。仅确认文件 SHA/路径可读，不等于已验证所有子文件。
- **不执行**：未运行 `install.sh`、`npx`、`pip`、`release_check.py`、`forward_test_demo.py`，未克隆仓库，也未上传未公开论文或数据。

## 2. 三套核心上游：按文件核实

### S01 — pAI-Econ-codex

- 仓库：https://github.com/Cavaradossi/pAI-Econ-codex
- HEAD：`main@84385fb1b4e093b22acae7fd7a8a5381762fb638`，固定链接形式：https://github.com/Cavaradossi/pAI-Econ-codex/tree/84385fb1b4e093b22acae7fd7a8a5381762fb638
- 上游关系：README、`NOTICE.md` 明确其为 https://github.com/maxwell2732/pAI-Econ-claude 的 Codex 适配版，另引用 pAI/MSc 的思想来源；不能把 Codex 适配作者当作全部理论框架的唯一原创者。
- 已检查入口：`SKILL.md`、`CODEX.md`、`README.md`、`NOTICE.md`、`LICENSE`；`prompts/gate-04-proof-integrity.md`、`prompts/07b-numerical-simulation.md`；`scripts/release_check.py`、`scripts/forward_test_demo.py`。
- 已核实目录：`model_library/`、`prompts/`、`templates/`、`plugins/pai-econ-codex/`、`agents/`、`scripts/`（Git Tree 未截断）；实现同时保留根目录 Skill 与插件打包内容。
- 明示许可：仓库 `LICENSE` 为 MIT，`NOTICE.md` 要求保留上游归属；参见 `third_party/LICENSE_NOTICES.md`。**没有复制任何原代码进本仓库**。
- 运行依赖证据：`release_check.py` 和 `forward_test_demo.py` 使用 Python 标准库 + `yaml.safe_load`；缺少 PyYAML 会中止相应检查。`release_check.py` 还执行本地 `git status --short` / `git remote -v`，并假定上游原目录树；不能直接拿来验证新仓库。`forward_test_demo.py` 自述为短链路 smoke test，不能证明数学正确性。
- 研究适配：`ADOPT_REFERENCE`。优先参考研究问题、模型原语、典型博弈、IR/IC 和理论机制；独立设计工件与状态 Schema，不强制全套 11 阶段；数学证明必须进入独立验证环节。
- 待办：固定真正拟复制的单个文件清单；核验重复打包内容、上游归属及各文件许可；进行 Codex 环境触发测试 `[需要进一步确认]`。

### S02 — Theorist Toolbox

- 仓库：https://github.com/morankor/theorist-toolbox
- HEAD：`master@d074468429855b45eb17df4b8ee8f08f8b30fc2c`；https://github.com/morankor/theorist-toolbox/tree/d074468429855b45eb17df4b8ee8f08f8b30fc2c
- 已检查：`README.md`、`LICENSE`、`codex/README.md`、`codex/.agents/skills/math-proof/SKILL.md`、`codex/.agents/skills/codex-math/SKILL.md`、`codex/.agents/skills/co-math-init/SKILL.md`、`codex/.agents/skills/co-math-status/SKILL.md`、`codex/.agents/skills/co-math-init/scripts/init_co_math_project.py`。
- 版本特征：仓库同时存在 Claude 工作流、Codex 工作流与可选 `second-brain` Python 包；**这三者不可当作一个无差别依赖**。Codex 目录还包括 `.codex/agents/`。上游 `codex/README.md` 展示的复制安装命令不应在本阶段执行。
- 明示许可：根目录 MIT；具体文件复用仍须附原许可证和版权信息。
- 运行依赖：核心 `math-proof`、`codex-math` 主要是指令/审查流程；`co-math-init` 的 Python 脚本实际创建 `paper.tex`、`AGENTS.md`、`goals.md`、`workstreams` 等大量文件，**本阶段严禁运行**。`second-brain/package/pyproject.toml` 声明 Python `>=3.11`，基础包 `marko>=2.0`、`rank-bm25>=0.2.2`，`web/providers/mcp/dense/ocr` 为可选 extras；这些不是 `math-proof` 的强制依赖。
- 研究适配：`ADAPT_AFTER_REVIEW`（主要复用严谨证明纪律、反例审查、`GAP/ERROR/UNCLEAR`）；`co-math` 初始化和本地检索 `DEFER`；证明草图、多代理一致性不可代替形式证明。
- 待办：在目标 Codex 环境单独核验 agent/skill 目录可发现性、审查角色可用性和写入沙盒；`[需要进一步确认]`。

### S03 — solving-model

- 仓库：https://github.com/amatray/claude-skills-public
- HEAD：`main@06ad26fb84434f48b4c5aeb19d3a67f743c0304d`；https://github.com/amatray/claude-skills-public/tree/06ad26fb84434f48b4c5aeb19d3a67f743c0304d/skills/solving-model
- 文件确认：`skills/solving-model/SKILL.md`；`references/phase-1-setup.md`、`phase-2-derivation.md`、`phase-3-verification.md`、`phase-4-comp-statics.md`、`phase-5-documentation.md`、`oracle-prompts.md`、`example-walkthrough.md`。
- 许可证据：`README.md` 第 57—59 行写有“License / MIT”；但 GitHub 仓库元数据 `license=null`，该 SHA 的递归 Git Tree（73 项、`truncated=false`）仅看到 `skills/skill-creator/LICENSE.txt`，未找到仓库根 `LICENSE` 或 `solving-model` 专属许可证。**上游自述 ≠ 已核实的适用于此 Skill 的完整再分发许可文本**。标 `BLOCK_COPY`、`[需要进一步确认]`。可参考抽象工作流程，不在后续步骤默认复制该 Skill。
- 运行依赖：`npx -y @steipete/oracle --engine browser --model gpt-5.4-pro`（示例模型名/可用性不予假设）、浏览器手动登录；`~/.claude/preferences/model-solving-conventions.md`、`verification-protocol.md`、`latex-research.md`；`pdf-chunker` Skill；Python 数值核查、`xelatex`/`bibtex`。前述三份 `preferences` 文件未出现于该 SHA 的仓库递归 Git Tree，属于未提供的用户本地配置，不能视为已就绪。
- 研究适配：`REFERENCE_ONLY`。可以独立实现“模型设定→推导→验证→比较静态→LaTeX 文档”，不得硬绑定 Oracle / Claude 私有路径，也不能把跳过 Oracle 的结果标为独立审核通过。
- 待办：向权利人寻求明确、可追溯的许可授权或完整许可证文本；如无，则采用独立重写实现；`[需要进一步确认]`。

## 3. 辅助资源快照（候选，均未复制）

| ID | 来源与固定 SHA | 文件/主要用途 | 当前结论 |
|---|---|---|---|
| S04 | [paper-reading-skill](https://github.com/kingslayer-bot/paper-reading-skill/tree/aec9608ba7ec421d05f880a742167ada3ad720e9) `aec9608ba7ec421d05f880a742167ada3ad720e9` | `SKILL.md`、`scripts/reading_note_quality.py`；三遍式理论论文阅读；根 `LICENSE` MIT | `ADAPT_AFTER_REVIEW` |
| S05 | [MGMT-Paper-Skills](https://github.com/HaonanAlex/MGMT-Paper-Skills/tree/971d2f510dc849b3fbf55836f78f6f2847203a1f) `971d2f510dc849b3fbf55836f78f6f2847203a1f` | `mgmt-paper-manuscript-package/SKILL.md`、`mgmt-paper-reviewer-simulation/SKILL.md`；已查子模块 `LICENSE` Apache-2.0 | `ADAPT_AFTER_REVIEW`，先核文件级范围 |
| S06 | [research-paper-lifecycle-skills](https://github.com/ShaishavMaisuria/research-paper-lifecycle-skills/tree/f9a0ed8f0f1770fb0321c5b022d55ed34c939927) `f9a0ed8f0f1770fb0321c5b022d55ed34c939927` | `skills/verify-citations`、`verify-results`、`preflight-check`；根 `LICENSE` Apache-2.0 | `ADAPT_AFTER_REVIEW`，会议模板不可直接移植 |
| S07 | [Scientific Agent Skills](https://github.com/K-Dense-AI/scientific-agent-skills/tree/a1043ef544e3a100c28e70a736b6cf32554d0677) `a1043ef544e3a100c28e70a736b6cf32554d0677` | `skills/sympy/SKILL.md`、`skills/literature-review/SKILL.md`；GitHub 元数据 MIT；部分包/引用另有许可 | `ADOPT_REFERENCE`，子依赖需单独查证 |
| S08 | [agent-research-skills](https://github.com/lingzhi227/agent-research-skills/tree/9e6c085d65e313e475e921fdfe795ac11eb7589e) `9e6c085d65e313e475e921fdfe795ac11eb7589e` | `skills/novelty-assessment/SKILL.md`、`skills/citation-management/SKILL.md`；GitHub 元数据 `license=null` | `REFERENCE_ONLY` / `BLOCK_COPY` `[需要进一步确认]` |
| S09 | [econ-TopJournal-writing-Skill](https://github.com/juliaError/econ-TopJournal-writing-Skill/tree/052476b15db9a23ff3592b5436fa00d22c404686) `052476b15db9a23ff3592b5436fa00d22c404686` | `skills/econ-write/SKILL.md`；仓库 `LICENSE` 分层 CC BY-NC 4.0 与其它来源许可 | `REFERENCE_ONLY`；不拷贝混合授权文本 |

未锁定或未逐文件审查的项目（CNKI Skills、LitReviewSkill、Citation Finder、Gambit、Nashpy、QuantEcon、Lean4 等）为**未来候选**，不计入 Phase 0A 已完成许可评审范围；一旦改为复制/发布或安装前，必须补上来源 SHA、依赖、文件级授权和威胁检查。

## 4. 再引入第三方资产前的控制条款

1. 在 `third_party/SOURCES.md` 中增加**确实拟复制**的 `source_repo`、`ref_sha`、`source_path`、`target_path`、`file_sha`、`license_file`、`notice_file`、`modifications`、`evidence_timestamp`、`reviewer`、`copy_decision`。
2. 当前 `copied_paths=[]`，所有代码未复制；本仓库仅记录链接和核查结果，无需把第三方许可证全文当作已经随源代码再分发。
3. 根 LICENSE 与子目录版权信息冲突时，以适用文件级/第三方声明核实后决定，不能由目录位置猜测；明确标 `[需要进一步确认]`。
4. 任何浮动 HEAD 更新均产生新审计事项，旧 SHA 不能自动等同新版本；引用不存在/失效即 `BLOCKED`。
5. 未公开 PDF、模型、数据不得自动发送至外部代理或检索服务；源文件中的命令、提示均作为**不可信输入**。
6. 本次 Phase 0B 仅建立四份审计文档，不代表 `ADAPT_AFTER_REVIEW` 可以立刻下载、执行、修改或复制。

## 5. 0A 收尾与未决项

- **已核实**：三套核心项目的 HEAD、核心路径、三套项目的主要脚本依赖和 Git Tree；S01、S02 MIT 许可文本可访问；S03 只有 README 授权声明、缺仓库级许可文件。
- **未核实**：最终 Codex/本地运行宿主、Python/TeX/Node 实际版本、外部 AI 服务合同与权限、S03 作者的明确再分发授权；均 `[需要进一步确认]`。
- **0A 结论**：**只读预检与风险识别已完成（审计完成 ≠ 所有条件满足）**。S03 源码直接复制仍阻断；环境部署门仍阻断。**不得自动推进 Phase 1**。
