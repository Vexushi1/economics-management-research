# LICENSE_NOTICES.md — 第三方版权、许可与再发布限制审计

> Phase 0B 文档审计 / 2026-10-12。关联：`SOURCES.md`、`docs/ENVIRONMENT_MATRIX.md`、`docs/DEPENDENCY_RISKS.md`、`MODIFICATION_PLAN.md`。  
> **警告：本仓库目前未复制第三方 Skill 源码，也未决定本仓库自有代码的最终 LICENSE。** 以下仅为许可证证据和未来拟复用范围审查，不构成法律意见，也不应作为“所有模块已经获得再发布许可”的证明。

## 1. 审查判定规则

| 代码 | 含义 | 采取动作 |
|---|---|---|
| `L-VERIFIED` | 已查看针对来源的实际许可文本及明确的授权/通知要求 | 未来可在遵守条件、核对文件级内容后考虑复制 |
| `L-DECLARED` | README/frontmatter 宣称某协议，但尚无可核实的适用完整许可文本 | 不作为直接再发布的充分依据，`[需要进一步确认]` |
| `L-CONDITIONAL` | 协议明确存在非商业、署名或其它限制，且具体用途尚不明确 | 不按 MIT/Apache 的权限默认操作 |
| `L-UNKNOWN` | 没有定位到明确授权或混合内容许可范围不清 | 直接复制 `BLOCKED` |
| `L-EXTERNAL` | 作为正常安装的外部库/服务使用，不把其源码并入本仓库 | 另行遵循所用版本的依赖、API 条款与许可证 |

注意：`L-VERIFIED` 仅表示已经查到许可证文件，**不能**替代逐文件来源、版权拥有者、第三方内嵌材料、商标与专利等审查；MIT/Apache 也不代表可以删除版权说明。

## 2. 核心三项：证据、许可、当前结论

### L01 pAI-Econ-codex — MIT 文本已核实

- 仓库：https://github.com/Cavaradossi/pAI-Econ-codex
- 固定提交：`84385fb1b4e093b22acae7fd7a8a5381762fb638`
- 文本：https://github.com/Cavaradossi/pAI-Econ-codex/blob/84385fb1b4e093b22acae7fd7a8a5381762fb638/LICENSE
- 上游告知：https://github.com/Cavaradossi/pAI-Econ-codex/blob/84385fb1b4e093b22acae7fd7a8a5381762fb638/NOTICE.md
- **证据**：`LICENSE` 明确写 MIT License，含 2026 年原项目/适配作者及其另行说明的历史来源；`NOTICE.md` 指明从 `maxwell2732/pAI-Econ-claude` 适配并要求保留上游归属。GitHub 元数据 SPDX 识别为 `NOASSERTION`，这是自动识别限制，**不推翻读取到的实际 MIT 文本**。
- **义务**：未来实质复制或发布源码时，应保留原版权声明与 MIT 许可文本；适用的上游 NOTICE 一并保留或记录，不得删改既有作者权利声明。若文件夹含第三方独立许可内容需逐项核查。
- 状态：`L-VERIFIED`（上游 LICENSE/NOTICE），**尚未批准或实施源码复制**。

### L02 Theorist Toolbox — MIT 文本已核实

- 仓库：https://github.com/morankor/theorist-toolbox
- 固定提交：`d074468429855b45eb17df4b8ee8f08f8b30fc2c`
- 文本：https://github.com/morankor/theorist-toolbox/blob/d074468429855b45eb17df4b8ee8f08f8b30fc2c/LICENSE
- **证据**：根 `LICENSE` 为 MIT，署名 Moran Koren；GitHub 仓库元数据也识别 MIT。`codex/`、`skills/`、`second-brain/package/` 的使用范围和是否涉及嵌入第三方内容，在**选择具体复制路径时**再次核实。
- **义务**：保留 MIT 版权和许可证告知；任何模型输出、引用论文或用户自有文档的版权不被该 MIT 自动授权。
- 状态：`L-VERIFIED`；`second-brain` 外部依赖各有独立许可证，不能直接继承根目录 MIT。

### L03 solving-model — ⚠️ 授权文本不足，禁止直接复制

- 仓库：https://github.com/amatray/claude-skills-public
- 固定提交：`06ad26fb84434f48b4c5aeb19d3a67f743c0304d`
- README：https://github.com/amatray/claude-skills-public/blob/06ad26fb84434f48b4c5aeb19d3a67f743c0304d/README.md
- Skill：https://github.com/amatray/claude-skills-public/tree/06ad26fb84434f48b4c5aeb19d3a67f743c0304d/skills/solving-model
- **可证实事实**：README 第 57—59 行声明 “License / MIT”；但 GitHub 仓库元数据 `license=null`，对固定 SHA 的 Git Tree 全量检查（`truncated=false`）未发现仓库根 `LICENSE` 或 `skills/solving-model/` 中的专属 MIT 文本；仅见 `skills/skill-creator/LICENSE.txt`（适用范围不可直接扩展到 solving-model）。
- **法律/工程判断**：README 可能表达许可意图，但缺少可核实的授权范围、完整条款文本及版权声明。审计不得把这一不完整证据冒充“已完成文件级许可确认”。
- **当前状态**：`L-DECLARED` + `BLOCK_COPY`，`[需要进一步确认]`。可以学习“设置→推导→验证→比较静态→文档”的抽象研究方法；**不得原样复制 `SKILL.md`、`references/*` 或 Oracle 模板**直到明确授权。
- **解除路径**：请求权利人补齐明确适用 `solving-model` 的许可证/授权（优先保留书面证据和 SHA），或完全独立编写自己的数学研究工作流。是否足以复用、如何引用受法律场景影响，不能依赖本审计直接下法律结论。

## 3. 其它候选与许可证边界

| 项目 | 已核实的来源/证据 | 目前处理 |
|---|---|---|
| [paper-reading-skill](https://github.com/kingslayer-bot/paper-reading-skill/tree/aec9608ba7ec421d05f880a742167ada3ad720e9) | 仓库根 `LICENSE` MIT | `L-VERIFIED`，拟复制文件仍需保留相应声明 |
| [MGMT-Paper-Skills](https://github.com/HaonanAlex/MGMT-Paper-Skills/tree/971d2f510dc849b3fbf55836f78f6f2847203a1f) | `mgmt-paper-manuscript-package/LICENSE` Apache-2.0，模块 `SKILL.md` 明示 Apache-2.0 | **模块级** `L-VERIFIED`，不据此推断整库 |
| [research-paper-lifecycle-skills](https://github.com/ShaishavMaisuria/research-paper-lifecycle-skills/tree/f9a0ed8f0f1770fb0321c5b022d55ed34c939927) | 根 `LICENSE` Apache-2.0 | `L-VERIFIED`，履行版权/NOTICE/修改说明义务 |
| [Scientific Agent Skills](https://github.com/K-Dense-AI/scientific-agent-skills/tree/a1043ef544e3a100c28e70a736b6cf32554d0677) | GitHub 仓库元数据 MIT；`sympy` Skill 中的 `license` 字段指向 **SymPy 自身许可** | `L-DECLARED`（本审计尚未逐行复核仓库级许可文本和所有嵌入文件），`[需要进一步确认]` |
| [agent-research-skills](https://github.com/lingzhi227/agent-research-skills/tree/9e6c085d65e313e475e921fdfe795ac11eb7589e) | GitHub 元数据 `license=null`，此前未定位到根 LICENSE | `L-UNKNOWN` / `BLOCK_COPY` `[需要进一步确认]` |
| [econ-TopJournal-writing-Skill](https://github.com/juliaError/econ-TopJournal-writing-Skill/tree/052476b15db9a23ff3592b5436fa00d22c404686) | 根 `LICENSE` 规定原创内容 CC BY-NC 4.0，第三方内容（例如原 MIT 来源）另外授权 | `L-CONDITIONAL`，未经非商业适用性与分文件核查不复制 |
| CNKI Skills、LitReviewSkill、Citation Finder、其它可选项目 | 本轮未完成 SHA 锁定和逐文件许可检查 | `L-UNKNOWN` / `DEFER`，不视为可直接复制 |

提示：Gambit、Nashpy、SymPy、SciPy、NumPy、Pandas、Matplotlib、QuantEcon、Lean 等未来作为外部依赖时，使用各自发行版本的正式许可和安全公告，不以某个第三方 Skill 的 frontmatter 取代它们自身的许可审查。**本轮没有逐一核对这些库的确切发行包许可证或建立 SBOM**，`[需要进一步确认]`。

## 4. 再发布与署名实施准则

1. **克隆权与发布权分离**：公共仓库可以用于合法查看/克隆，但并不自动允许复制到另一个公开仓库、修改后再分发，更不自动允许删除原作者署名。
2. **独立实现与衍生复用分离**：只研究通用经济学原理、标准数学方法和抽象流程，然后独立编写实现，不等于复制受到保护的具体代码和文字；但不能把“换几个变量名”包装成独立重写。
3. **版权声明位置**：如实际复制 MIT/Apache 代码，应在适用的 `LICENSE`、`NOTICE`、`third_party` 文件中保留法定声明、复制路径、来源 SHA、修改标记；无需在主页宣传原作者，但不能删除必须保留的信息。
4. **Apache-2.0**：除许可证副本外，注意适用的版权及 NOTICE 内容、修改说明和适当的专利条款；具体以适用发行版条款为准。
5. **CC BY-NC 4.0**：必须核实用途是否符合非商业性及正确署名等要求；不能仅因仓库 Public 就认为允许无限制商用再发布。
6. **用户上传论文**：第三方论文 PDF、原始图表、付费数据库内容与用户未公开研究数据各有独立版权/隐私义务，不能随 Skill 源码任意再发布。
7. **尚未选定本项目代码许可证**：自有新代码采用 MIT、Apache-2.0 等仍为用户决策 `[需要进一步确认]`；不可提前写出 `LICENSE` 或据此承诺兼容性。

## 5. 许可放行检查表（Phase 1 之前）

- [x] 核对核心三套项目的固定 SHA、源文件和 README/许可证证据。
- [x] 将 `solving-model` 明确列为 `BLOCK_COPY`，不掩盖“README 宣称 MIT、许可证文本缺失”的差异。
- [ ] `[需要进一步确认]` 权利人明确授权或确认仅独立重新实现 solving-model 流程。
- [ ] `[需要进一步确认]` 确认公开发布 / 未来商业用途策略与新仓自有 LICENSE。
- [ ] `[需要进一步确认]` 对拟复制的**具体**第三方文件进行逐文件版权/NOTICE 复核。
- [ ] `[需要进一步确认]` 拟引入的外部 Python/CLI 库实际发行版本和许可证核实。

**结论**：许可来源审查记录已落地；S01、S02 有 MIT 文本依据，S03 仍不能直接复制。**Phase 0B 完成不意味着这些阻断项自动解除，也不意味着 Phase 1 获得实施授权。**

## Phase 1 dependency license record (2026-10-12)

- The owner-selected license for this repository's new original code is **MIT**, see root `LICENSE`. This does not relicense third-party material.
- GitHub Actions generated `requirements/ci-py312-linux.lock` for Ubuntu 24.04 x86_64 / Python 3.12. It contains exact direct and transitive versions and SHA-256 distribution hashes. CI uses `--require-hashes --only-binary`.
- Direct dependencies: jsonschema 4.26.0 (MIT), SymPy 1.14.0 (BSD), NumPy 2.3.5 (BSD-style with bundled third-party notices); test tooling pytest 9.0.2 (MIT), Ruff 0.13.2 (MIT); build tooling setuptools 82.0.1 (MIT) and wheel 0.45.1 (MIT).
- Resolved transitive dependencies: attrs, iniconfig, jsonschema-specifications, mpmath, packaging, pluggy, pygments, referencing, rpds-py, typing-extensions. **Full transitive license-text audit and SBOM remain [需要进一步确认]**, and no dependencies were copied into this repository.
- Exact versions and distribution hashes mitigate drift and substitution; they do not eliminate compromised upstream releases, mutable infrastructure or runtime vulnerabilities.
- `solving-model` remains **BLOCK_COPY**; only independent clean-room logic is allowed.
