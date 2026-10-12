# Economics & Management Research — 深度整合与实施蓝图

> **文档属性**：Planning Only / RFC（拟议架构，未经执行验收）  
> **文档版本**：Reviewed Draft v0.3（独立二次审计修订；非运行验收）  
> **编制日期**：2026-10-12  
> **目标仓库**：[Vexushi1/economics-management-research](https://github.com/Vexushi1/economics-management-research)  
> **当前入库路径**：`MODIFICATION_PLAN.md`（仓库根目录）  
> **已确认远程基线**：初始文件已于 2026-10-12 上传 `main`，基线 Commit `44d0d3f7d68b64e5fb57399dab03faa3cfee0ef8`，原 Blob `f3cf7259f08899208e7eef90fff40649f53982a7`；此处仅为本轮审查开始时的历史快照，修订提交后以远程 HEAD 为准。  
> **授权范围**：用户批准上传计划并要求最终审查；本轮文档修正只作用于这一个 `MODIFICATION_PLAN.md`。**仍不授权写入任何 Phase 0 业务/管理文件、执行 Phase 1 及后续开发或创建 PR**。  
> **Phase 0 边界**：仅允许进行 Phase 0A 只读核查；Phase 0B 的审查文档入库属于独立后续写入，须明确授权。

---

## 0. 事实、范围及变更控制

### 0.1 基线事实（已只读核验）

- **初次审查时**目标仓库是 `size=0` 的空仓库（历史事实）；**当前**仓库为 Public、默认分支 `main`，只包含 `MODIFICATION_PLAN.md`，且已核对目录 Contents API。当前仍**没有业务代码、接口、运行配置或测试**，因此是“仅文档仓库的分阶段初始化”，不是既有业务代码重构。后续执行前再次获取 HEAD，不能沿用历史空仓库状态。
- 已通过 GitHub 只读接口核对关键上游仓库、入口 `SKILL.md`、若干 `references/`、`prompts/`、模型库、工具/脚本与许可文本；**尚未下载整库、执行第三方脚本、安装依赖或做端到端测试**。
- 本 RFC 的接口名称、Schema、目录路径、入口命令等，是**拟定的新项目规范**；凡涉及实际运行环境、包兼容性、API 授权及预期数学结果尚待实测的部分，一律标 `[需要进一步确认]`。
- 本项目所需论文范式至少覆盖：解析型 Stackelberg/Nash/Hotelling、委托代理与合同协调、动态/微分博弈、随机供给及库存优化、计量实证、理论与实证结合。以上是从用户给出的 2021—2026 年直播电商论文中提炼的**需求范畴**，不是宣称已有论文已被机器复现。

### 0.2 当前不可触碰的边界

- 本轮仅允许对**同一份** `MODIFICATION_PLAN.md` 做受审计驱动的文档纠错及必要 GitHub 更新；**禁止新增其它文件、修改业务代码/配置、创建 PR 或分支**。既有单次初始化 Commit 为历史事实，不再被表述为仍待执行。
- 后续实施必须由用户单独授权；本 RFC 不构成实施授权。
- 对上游项目，仅作只读研究；不得因为“公开可克隆”就删除版权、许可证或作者署名。
- 学术原始 PDF、未公开稿件、企业微观数据与凭据不得无授权上传 GitHub 或第三方服务。

### 0.3 术语约定

- **Skill**：以 `SKILL.md` 及其必要资源组成的任务规范；不等于真实数学求解引擎。
- **Adapter**：包装外部计算工具或服务的薄接口；可以替换实现。
- **Verified**：需在具体对象与特定范围内定义，不能把“AI 自审通过”当作数学严格证明或实证因果识别成功。
- **Replication**：独立重建论文的模型/代码/图表并比较结果；**一致性检查**、**可运行**与**完全复现**是三种不同结果。
- **Stage**：研究生命周期中的逻辑阶段；不是必须线性强制执行的提示词链。
- **Gate**：交付物达到特定证据标准的检查，不得随意把未证明命题标为 PASS。

---

## 1. 现状评估与最终目标

### 1.1 现状与现实问题

由于目标仓库**目前只有本计划文档、没有任何业务代码**，仍不存在可评估的既有业务接口、配置与运行时兼容性；需要解决的是设计层面风险：

1. 多个开源仓库都能做文献或写作，若整库导入，会发生命令重名、重复检索、不同输出字段冲突、重复调用大模型。
2. pAI-Econ、solving-model、Theorist Toolbox 的产物不同：经济学研究假设/证明草图/独立证明审查不能直接互相替代。
3. 普通科研 Skill 偏向回归或机器学习，缺少连续策略博弈的可行域、全局最优、分段边界解、均衡概念与合同约束的专门审计。
4. 写作系统可能把未经核验的数值、引用和命题转述为确定事实。
5. 一些上游流程依赖特定 Claude/Codex 目录、外部 Oracle CLI 或其它仓库的脚本；直接复制 `SKILL.md` 不保证可运行。
6. 公开仓库整合第三方 Skill 时有许可证、署名、非商业限制、数据隐私与可复现性问题。
7. 若每个失败都从头运行完整科研流程，会造成重复 API 费用和状态污染。

### 1.2 业务目标（按优先级）

- **B1**：支持从商业现象 → 研究问题 → 文献定位 → 原创性初筛 → 经济机制建模 → 均衡与命题 → 数值/实证验证 → LaTeX 论文 → 投稿检查的全生命周期。
- **B2**：理论分析/随机优化/计量实证/混合研究分路由；任何论文不必运行无关算法。
- **B3**：可对用户指定论文执行精读、公式抽取、独立重新推导、反例搜索、参数敏感性分析与可追溯复现。
- **B4**：每一项论文主张能追溯到来源文本、证明对象、运行记录或可靠估计；不伪造 DOI、结果和创新性保证。
- **B5**：支持 Omega、IJPE、JRCS、ECR、AOR、MDE 等**期刊风格的可配置模板**；不把单一期刊/固定 7 章当成通用学术规范。
- **B6**：对用户现有已上传论文建立可扩展的文献库；真实 PDF 默认存于私有/本地项目区而非公开仓库。

### 1.3 技术目标

- **T1**：一个最小 `research-orchestrator` 协调入口，若干独立 `SKILL.md`；模块通过版本化 Schema/工件交换数据，不依赖隐式对话记忆。
- **T2**：任务输出带来源、假设、版本、工具、参数域、证据状态和不确定性说明。
- **T3**：执行计算优先本地 SymPy/SciPy；外部模型/计算器为可选适配器，失败后可降级，不自动泄露未公开数据。
- **T4**：支持增量重新运行：按输入哈希、模块版本和依赖记录决定失效范围，不重跑无关已验收步骤。
- **T5**：测试覆盖静态规范、Schema 契约、解析均衡、数值鲁棒性、引用一致性、论文编译和可复现实验。
- **T6**：可安装、可验证、可回退；每个增量阶段保持已有测试通过。

### 1.4 明确不追求

- 不构建“自动保证能发 SSCI 的论文生成器”。
- 不将自动生成的证明草图称为严格证明。
- 不默认执行第三方爬虫、付费 API、模型上传或任意 Skill 中的 shell 命令。
- 不整库复制不相干模块；不删除必须保留的作者与许可证信息。
- 不使用未经核验的期刊分区来控制论文质量或发表预期。

---

## 2. 上游依赖与 Skill 选择（有依据的工程决策）

### 2.1 核心组件：上游已核查的快照

以下 SHA 是本次只读获取的**分支最新提交快照**，仅用于可追溯参考；首次复用时应锁定并重新确认，不自动追踪 HEAD。

| 上游 | 分支 / 本次快照 | 核查到的事实 | 适配决策 | 主要缺点及风险 |
|---|---|---|---|---|
| [pAI-Econ-codex](https://github.com/Cavaradossi/pAI-Econ-codex) | `main` `84385fb1b4e093b22acae7fd7a8a5381762fb638` | `SKILL.md`、`prompts/`、`model_library/`、`templates/`、`scripts/`；MIT 许可（保留上游与其原作者版权） | **采用模型库/理论谱系/现实性检查；不照搬 11 阶段为总调度** | Proof Gate 只审证明草图，并不保证证明完成；数值阶段原版须额外批准；深层路径与旧命名需适配 |
| [Theorist Toolbox](https://github.com/morankor/theorist-toolbox) | `master` `d074468429855b45eb17df4b8ee8f08f8b30fc2c` | `codex/.agents/skills/` 中可核实 `math-proof`、`codex-math`、`co-math-init`；MIT | **采用命题审查、反例查找及未证明义务机制** | 多 Agent 耗时；部分路径基于特定环境；自审无法取代正式逻辑证明 |
| [solving-model](https://github.com/amatray/claude-skills-public/tree/main/skills/solving-model) | `main` `06ad26fb84434f48b4c5aeb19d3a67f743c0304d` | 5 阶段 `SKILL.md` 和 `references/phase-*.md`；README 标示 MIT | **采用设定→推导→验证→比较静态→文档流程，重写工具层** | 引用 `@steipete/oracle`、`~/.claude/preferences/`，这些不是可移植默认依赖；仓库根目录许可文件情况 `[需要进一步确认]` |
| [paper-reading-skill](https://github.com/kingslayer-bot/paper-reading-skill) | `main` `aec9608ba7ec421d05f880a742167ada3ad720e9` | `SKILL.md` 三层阅读模式与本地质量脚本，MIT | **采用三层精读策略，扩展经管模型记录表** | 论文解释不等于可复现或证明，扫描 PDF 需保留页码与不确定性 |
| [MGMT-Paper-Skills](https://github.com/HaonanAlex/MGMT-Paper-Skills) | `main` `971d2f510dc849b3fbf55836f78f6f2847203a1f` | `mgmt-paper-manuscript-package`、审稿模拟，相关子模块 Apache-2.0 | **采用写作材料包、证据矩阵与独立预审** | Beta 模块；论文结构规则需要按目标期刊校准 |
| [research-paper-lifecycle-skills](https://github.com/ShaishavMaisuria/research-paper-lifecycle-skills) | `main` `f9a0ed8f0f1770fb0321c5b022d55ed34c939927` | `verify-citations`、`verify-results`、`preflight-check`，Apache-2.0 | **采用引用/结果/投稿检查方法** | 部分默认模板偏计算机会议；不能原样覆盖期刊 |
| [Scientific Agent Skills](https://github.com/K-Dense-AI/scientific-agent-skills) | `main` `a1043ef544e3a100c28e70a736b6cf32554d0677` | `literature-review`、`sympy` 等，相关技能声明 MIT；具体模块依赖不同 | **选用通用文献流程及符号运算规范** | 文献数据库部分偏医学；OpenRouter 等外部组件为可选，不能强制 |

上表**不意味着上游所有代码均已审查安全或许可证逐文件齐全**。`SOURCES.md` 应继续逐个记录文件级许可证、SHA、第三方引用与可使用范围。

### 2.2 其它已检索来源：采用/参考/暂不整合

| 项目 | 用途 | 推荐状态 | 理由 |
|---|---|---|---|
| [agent-research-skills](https://github.com/lingzhi227/agent-research-skills) | 新颖性、多轮检索、文献管理 | 参考流程、独立实现 | 部分 Skill 引用其它技能脚本路径；根目录 LICENSE 状态 `[需要进一步确认]` |
| [LitReviewSkill](https://github.com/Zsun79/LitReviewSkill) | 中文/英文文献整理 | 仅参考 | 实际爬取权限和许可证 `[需要进一步确认]` |
| [econ-TopJournal-writing-Skill](https://github.com/juliaError/econ-TopJournal-writing-Skill) | 经济学写作 | 参考规范，避免整库复制 | 原创内容 CC BY-NC 4.0，部分第三方内容授权不同；商业用途需审查 |
| [Auto-Empirical-Research-Skills](https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills) | 计量/因果推断 | 后期分支参考 | 理论博弈项目不应强制计量流程；仓库集合内容可能有多重许可证 |
| [CNKI Skills](https://github.com/cookjohn/cnki-skills) | CNKI 检索 | 后期可选接入 | 访问权限、自动化合规、浏览器依赖及许可待审 |
| [Citation Finder](https://github.com/HuiyuLi-2000/citation-finder) | 论断支持文献推荐 | 可选候选 | 需将“找到文献”与“文献支持论断”分开核验 |
| [Humanizer](https://github.com/blader/humanizer) | 语言修饰 | 非核心 | 不以规避检测为目标；不得改写事实、公式、引文 |
| [Introduction Skill](https://github.com/shenaowu0915-SIM/introduction-skill) | 引言布局 | 方法参考 | 原版偏工程背景；需按经管理论贡献重做 |
| [Awesome-Journal-Skills](https://github.com/brycewang-stanford/Awesome-Journal-Skills) | 期刊风格 | 参考资料 | 不能代替目标期刊官网 Author Guidelines |
| [Gambit](https://github.com/gambitproject/gambit)、[Nashpy](https://github.com/drvinceknight/Nashpy)、[QuantEcon.py](https://github.com/QuantEcon/QuantEcon.py) | 有限博弈、动态模型 | 外部依赖候选 | 对连续策略 Stackelberg 不自动通用；按模型类型开启 |
| [Lean4 Skills](https://github.com/cameronfreer/lean4-skills) | 形式化证明 | 后期可选 | 经济模型转写工作量大；不应默认强制 |
| PPT、Speaker、中文毕业论文排版、特定站点爬虫 | 教学展示或非核心交付 | 不进入核心 | 属于支线功能，过早整合增加维护与合规成本 |

### 2.3 不重复造轮子的边界

- **复用内容**：经济理论模型原语、严谨数学审查纪律、PDF 阅读策略、引用元数据校验、投稿清单。
- **独立开发内容**：统一研究工件 Schema、模型/命题/证明的证据状态、依赖图与增量执行、连续博弈优化器适配、合同协调专门审计、论文复现的来源追溯。
- **调用外部库而非复制源码**：SymPy、SciPy、NumPy、Pandas、Matplotlib；Gambit/Nashpy/QuantEcon 按需。
- **不强制绑定服务**：Claude、OpenAI、Oracle、Zotero、Semantic Scholar、Crossref 等都通过可选 Adapter；需明确联网与数据发送授权。

### 2.4 许可证实施原则

1. MIT/Apache 可按其条款复用和修改，但必须保留规定的版权/许可证/NOTICE；衍生代码加自有贡献声明不能删除原作者声明。
2. CC BY-NC 与 MIT/Apache 不能简单视为同样的自由复用条件；在不确定最终商业用途时先只使用通用思想、独立撰写实现。
3. 没有 LICENSE 不等于获得再分发许可；优先使用 API/外部安装或独立实现。`[需要进一步确认]` 的许可不得安排为直接复制来源。
4. 第三方 PDF 原文、截图、表格与图像受独立版权约束；科研笔记应保存引用与最小必要摘录。
5. 在后续 `third_party/SOURCES.md` 中每项写：`repo_url`、`commit_sha`、`copied_paths`、`license`、`notice_path`、`modifications`、`review_status`、`retrieved_at`。

---

## 3. 目标架构与职责边界

### 3.1 生命周期与路由

`intake → research-framing → literature-intelligence → research-design → (analytical-game | stochastic-operations | empirical-econometrics | hybrid) → verification/replication → manuscript → submission-audit`

- **按任务进入**：用户可直接要求“复现某论文 Figure 2”而不必跑完整选题→写作。
- **按模型进入**：用户提供 `model-spec` 后直接执行求解和证明，绝不要求重新进行文献检索。
- **增量依赖**：仅输入/版本变化的工件及其下游失效，保留已验证上游结果。
- **单一写入所有者**：理论假设由 model-design 管理；推导由 solver 管理；审查者只出审查报告，不暗中改写结论；写作模块只引用核验后的结论。
- **人工确认**：选题与模型假设基线批准、外部传输或高成本执行、投稿正式交付须用户批准；普通符号推导无需逐式停顿。

### 3.2 目标目录树（除现有 `MODIFICATION_PLAN.md` 外均为拟新增；按各 Phase 文件表汇总）

```text
.github/
  workflows/
    validate.yml
docs/
  CHANGELOG.md
  DEPENDENCY_RISKS.md
  ENVIRONMENT_MATRIX.md
  OPERATIONS.md
  RELEASE_CRITERIA.md
  SECURITY.md
examples/
  paper-replication/
    README.md
  contract-coordination
  stackelberg-baseline
references/
  economic-model-library/
    README.md
    platform-hotelling.md
    principal-agent.md
    stackelberg.md
  journal-profiles/
    README.md
schemas/
  equilibrium-result.schema.json
  literature-matrix.schema.json
  model-spec.schema.json
  paper-record.schema.json
  proposition.schema.json
  replication-report.schema.json
  research-state.schema.json
  verification-report.schema.json
skills/
  academic-writing/
    SKILL.md
  citation-audit/
    SKILL.md
  contract-mechanism/
    SKILL.md
  dynamic-optimal-control/
    SKILL.md
  econometric-analysis/
    SKILL.md
  economic-model-design/
    SKILL.md
  game-equilibrium/
    SKILL.md
  literature-review/
    SKILL.md
  paper-reading/
    SKILL.md
  paper-replication/
    SKILL.md
  research-novelty/
    SKILL.md
  research-orchestrator/
    SKILL.md
  stochastic-optimization/
    SKILL.md
  submission-review/
    SKILL.md
  theorem-verification/
    SKILL.md
src/
  emr/
    adapters/
      bibliography.py
      numerical_scipy.py
      symbolic_sympy.py
    core/
      artifacts.py
      cache.py
      contracts.py
      provenance.py
      registry.py
      router.py
    domain/
      contract.py
      dynamic.py
      econometrics.py
      game.py
      manuscript.py
      proof.py
      replication.py
      stochastic.py
    __init__.py
    cli.py
templates/
  empirical-paper/
    main.tex
  research-project/
    README.md
    literature-matrix.md
  theoretical-paper/
    main.tex
    proof-appendix.tex
    references.bib
tests/
  fixtures/
    contract_coordination
    differential_state
    stackelberg_linear
    stochastic_supply
    synthetic_panel
  integration/
    test_incremental_execution.py
    test_latex_compile.py
    test_literature_offline.py
    test_minimal_workflow.py
    test_proof_audit.py
    test_replication_baseline.py
    test_security_boundaries.py
    test_stackelberg_end_to_end.py
  unit/
    test_artifacts.py
    test_best_response.py
    test_citation_integrity.py
    test_contract_conditions.py
    test_corner_cases.py
    test_counterexample.py
    test_dynamic_timing.py
    test_empirical_claims.py
    test_game_spec.py
    test_information_sequence.py
    test_manuscript_consistency.py
    test_paper_record.py
    test_proposition_state.py
    test_provenance.py
    test_registry.py
    test_router.py
third_party/
  LICENSE_NOTICES.md
  SOURCES.md
.gitignore
AGENTS.md
LICENSE
MODIFICATION_PLAN.md
README.md
pyproject.toml
```

注意：除 `MODIFICATION_PLAN.md` 已在仓库根目录，其余均为**拟议文件变更清单**，不是读取到的现有文件。所有接口定义见下一节；路径可依据后续初步 PoC 调整，并在变更记录中说明。[需要进一步确认] Agent Skills 的运行宿主（ChatGPT/Codex/Claude/本地 CLI）及平台细节；第一版以纯 Markdown + Python 可测试模块为最低公分母。

### 3.3 跨模块接口（拟议规范，不代表已存在）

**统一入口：**

```python
# src/emr/core/router.py — 未来建议 API，尚未实现
from dataclasses import dataclass

@dataclass(frozen=True)
class ResearchRequest:
    task_type: str       # e.g. "model.solve", "paper.replicate"
    project_id: str
    artifact_refs: tuple[str, ...]
    options: dict        # validate against a versioned schema

# def route_request(request: ResearchRequest, registry: "SkillRegistry") -> "ExecutionPlan": ...
```

**每个 Skill 的跨宿主 frontmatter 最小公共字段**：`name`、`description`。`input_artifacts`、`output_artifacts`、`required_tools`、`optional_tools`、`safety_notes`、`compatible_research_types` 属于本仓扩展元数据，优先存放在独立的版本化注册表，或在经宿主兼容性验证后放入受支持的 `metadata` 字段；**不得假定所有 Codex/Claude/其它宿主都接受顶层自定义 YAML 字段**。`required_tools` 为抽象能力如 `symbolic.algebra`，而非指定品牌 CLI。

**模型输入（示例）**：

```yaml
schema_version: '0.1.0'
model_id: example-stackelberg
research_type: analytical_game
players: [leader, follower]
sequence:
  - {stage: 1, actor: leader, decision: price}
  - {stage: 2, actor: follower, decision: effort}
information: {observability: complete}
decisions:
  - {name: price, domain: nonnegative_real}
  - {name: effort, domain: nonnegative_real}
parameters: []
objectives: []           # 必须填入后才能求解
constraints: []
equilibrium_concept: subgame_perfect_equilibrium
source_refs: []
```

**特别说明**：这一 YAML 仅用于说明字段，因 `objectives` 为空，不是一个可运行博弈。未来校验器必须拒绝缺失利润/目标函数的 `model-spec`。

**求解返回（拟议）**：

```python
# src/emr/core/contracts.py — 未来建议 API
@dataclass(frozen=True)
class SolveResult:
    model_id: str
    solution_status: str    # CANDIDATE_STATIONARY_POINT | EQUILIBRIUM_CHECKED | MULTIPLE_EQUILIBRIA | INFEASIBLE | UNSUPPORTED | UNRESOLVED
    solution_method: str    # SYMBOLIC | NUMERICAL | HYBRID | NOT_RUN（不同于验证/证明状态）
    equilibria: tuple[dict, ...]
    parameter_conditions: tuple[str, ...]
    residuals: dict
    certificates: dict      # concavity, KKT, global best responses, etc.
    tool_versions: dict
    evidence_refs: tuple[str, ...]
```

**不得把** `SYMBOLIC` 或 `NUMERICAL` 这类求解方式与 `PROVED_WITH_STATED_ASSUMPTIONS`、`FORMALLY_CHECKED` 等证明状态混为一谈。`EQUILIBRIUM_CHECKED` 只表示在报告记录的范围、参数域及验证标准下完成了均衡检查；**不自动代表全局、唯一或形式化证明**。`SolveResult` 说明找到了什么，`VerificationReport` 说明验证范围和不确定性。论文写作仅允许引用带明确证据状态的结果。

### 3.4 研究状态及证据分类

- 项目研究进度：`IDEA / LITERATURE_SCREENED / MODEL_SPECIFIED / MODEL_APPROVED / DERIVED / VERIFIED / WRITING / READY_FOR_REVIEW / SUBMISSION_READY`；并行子任务可单独推进。此枚举**不得替代**独立工件有效性。
- 工件生命周期：`DRAFT / APPROVED / STALE / REVOKED / ARCHIVED`，由版本与依赖变化触发；`STALE` 不是“数学证明为假”，而是当前结果不再对应最新有效输入。后续 `artifacts.py`/`research-state.schema.json` 须分别实现两条状态轴。
- 证明状态：`UNEXAMINED / SKETCH / NUMERICALLY_SUPPORTED / PROVED_WITH_STATED_ASSUMPTIONS / FORMALLY_CHECKED / REFUTED / UNRESOLVED`。
- 引用元数据状态：`METADATA_UNVERIFIED / METADATA_VERIFIED / METADATA_INACCESSIBLE`；**独立**论断支持状态：`NOT_VERIFIED / CLAIM_SUPPORTED / CLAIM_UNSUPPORTED / INACCESSIBLE`。单篇 DOI 验证成功不得给与它关联的所有论断自动打上支持标签。PDF 提取状态另设 `READABLE / PARTIAL / UNREADABLE`。
- 复现状态：按模型、均衡、命题、表格、图分别存 `MATCH / PARTIAL / MISMATCH / NOT_RUN / UNREPRODUCIBLE_INPUT`。
- 求解可用性：`UNSUPPORTED` 表示能力未实现或工具不支持；它不同于数学上已证明的 `INFEASIBLE`。求解器返回 `EQUILIBRIUM_CHECKED` 仍须带验证范围、是否仅数值局部检查及均衡选择规则，不能单独表示严格全域成立。
- **状态单向证据约束**：`NUMERICALLY_SUPPORTED` 不自动升级为 `PROVED_WITH_STATED_ASSUMPTIONS`；AI 多轮一致不自动升级为 `FORMALLY_CHECKED`。

---
## 4. 分阶段实施路径与逐文件变更清单

> 除根目录已有的 `MODIFICATION_PLAN.md` 外，下述路径均为后续**拟新增**文件。`M` 表示未来实施阶段可能修改此前阶段建立的文件；`D` 表示可能移除过时文件。**尚未进行任何 Phase 0—9 的工程文件改动**；本文件的初始化/审计修订提交不应冒充开发阶段 Commit。阶段验收必须单独确认，分支/PR 仅在明确授权后执行。

### Phase 0 — 来源、许可与运行环境审查（0A 只读核查；0B 文档落地）

**目标**：消除“不知道 Skill 可否合法复用、环境是否可调用”的不确定性；不编写业务逻辑。

**子阶段边界**：`0A READ_ONLY`：查 GitHub HEAD/许可证、检查上游 SKILL 与 scripts、记录环境能力，不产生 GitHub 写入；`0B DOCUMENTATION`：在授权后提交下面四份审计文档。**本轮最多启动 0A，不能把 0B 写入视为已获授权。**

**建议文件（全部属于 0B；不可在 0A 中提交）：**

| 操作 | 拟议路径 | 文件内部需包含的内容 |
|---|---|---|
| A | `third_party/SOURCES.md` | 上游清单、commit SHA、精确引用路径、许可、适配决策、审查日期、替换策略 |
| A | `third_party/LICENSE_NOTICES.md` | 第三方版权声明与再发布要求；仅针对实际复用部分 |
| A | `docs/ENVIRONMENT_MATRIX.md` | Python/TeX/Codex/平台工具能力矩阵：必须/可选/不可用/待证实 |
| A | `docs/DEPENDENCY_RISKS.md` | API、CLI、外部访问、Secrets、上传、许可证风险条目 |

**执行任务：**

- 0.1 对每个计划复用的源文件固定上游 SHA 和许可证；**没有清晰授权则不得计划直接复制文件**。
- 0.2 分类 `prompt-only / script-backed / external-service / library-wrapper`；记录入口与 `scripts/`、`references/` 的路径依赖。
- 0.3 检查上游是否包含硬编码 `~/.claude/...`、`oracle`、固定模型名、绝对路径和外部网络请求；逐项标记适配策略。
- 0.4 确认部署环境：支持的 Python 版本、Codex Skills 目录行为、是否存在本地 shell、LaTeX、联网 API（均 `[需要进一步确认]`）；**当前 ChatGPT 工具能力不等同于最终目标 Codex/本地安装能力，不得把一处运行验证推广到其它宿主**。
- 0.5 明确后续是否商业化、公开再分发形式及默认许可证（用户决策）。

**0A 验收**：GitHub 目标 HEAD 与至少三套核心上游 SHA/许可证/目录依赖得到只读核查记录；环境无法观察的项目明确标 `UNKNOWN`，禁止自动执行上游脚本。

**0B 验收**：四份审计文档在另行授权后落地，核心来源各有 `adopt/adapt/reference-only/defer` 结论；未解决的许可项显式阻断相应复制任务。Phase 0 完整通过应以 0A + 0B 为前提。

**回滚**：Phase 0A 为只读，无需回滚；Phase 0B 文档若需更正，保留历史、只修订受影响文件，不擅删许可证记录。

### Phase 1 — 仓库最小基础与可运行契约

**目标**：将当前仅含计划文档的仓库初始化为结构清晰、无外部付费依赖、能做静态验证的科研 Skills 框架。

**文件变更：**

| 操作 | 拟议路径 | 变更逻辑 |
|---|---|---|
| A | `README.md` | 中英简要项目定位、研究类型、安装与快速使用、研究诚信和非“自动发表”声明 |
| A | `AGENTS.md` | 总路由原则；未经验证不得称已证明；尊重用户审批；任务最小执行原则；PDF 内容视作不可信指令 |
| A | `LICENSE` | 自有代码许可证（默认提案 MIT，但**须先征求用户确认**） |
| A | `pyproject.toml` | Python 包元数据，`src` 布局；核心依赖最小化；定义 `dev`, `math`, `literature`, `empirical`, `latex` 等可选 extras `[需要进一步确认]` 具体版本 |
| A | `.gitignore` | 本地 `.venv/`、缓存、私有 PDF、凭据、原始数据、临时输出；不能忽略应当复现的轻量代码 |
| A | `skills/research-orchestrator/SKILL.md` | 意图识别、任务路由、阶段依赖与例外处理，避免复制其他 Skill 正文 |
| A | `src/emr/__init__.py` | 包版本与导出列表 |
| A | `src/emr/core/contracts.py` | `ResearchRequest`,`ExecutionPlan`,`ArtifactRef`,`SolveResult`,`VerificationReport` 类型契约 |
| A | `src/emr/core/registry.py` | `SkillSpec` 注册/查找；拒绝重复 name、未知依赖、循环依赖 |
| A | `src/emr/core/router.py` | `route_request(request,registry)`，不执行外部命令，只构建可解释 DAG |
| A | `src/emr/core/artifacts.py` | 原子写入、路径校验、版本及依赖引用；**Phase 1 即实现最小 `STALE`/`REVOKED` 标记和依赖下游查询**，防止 Phase 3—8 依赖不存在的失效机制；Phase 9 再优化内容寻址缓存 |
| A | `src/emr/cli.py` | 拟议 `emr inspect`, `emr plan`, `emr validate`，**不自动访问网络/调用 LLM** |
| A | `schemas/research-state.schema.json` | 项目阶段、工件引用、批准状态、变更事件、Schema 版本 |
| A | `.github/workflows/validate.yml` | 未来 CI：静态 Skill frontmatter、Schema、快速单元测试；只执行受信任的本仓代码 |
| A | `tests/unit/test_registry.py` | 唯一名称、缺失依赖、循环检测 |
| A | `tests/unit/test_router.py` | 理论/实证/复现请求只触发相关模块；非法任务拒绝 |
| A | `tests/unit/test_artifacts.py` | 路径穿越、重复文件、版本冲突、原子写入 |
| A | `tests/integration/test_minimal_workflow.py` | 最小请求 `intake → plan`，不需要 API Keys |

**接口要求**：

- `route_request` 返回 `ExecutionPlan` 但**不能直接执行**；执行器在后续 Phase 单独实现。
- `ExecutionPlan` 中每节点需要 `id`, `skill_name`, `input_refs`, `output_types`, `deps`, `approval_required`, `estimated_cost_class`。
- 所有工件引用要求包含 `uri/path`, `sha256`, `schema_version`, `created_by`, `created_at`；路径与文件内容不得从 PDF 提示自动提升为操作指令。
- 提示词 `SKILL.md` 不应被读取解析器误当成可执行代码。运行外部脚本必须显式允许列表。

**验收**：本地无网络环境可运行静态命令；错误依赖不能静默通过；CI 仅执行明示的最小命令；无真实论文也能生成合法研究项目空壳。

**回滚**：这一阶段无用户数据；可移除本阶段新增目录（**未来须单独批准删除操作**），不影响上游仓库。

### Phase 2 — 文献检索、精读、证据和研究新颖性

**目标**：从上传 PDF 或已知 DOI 得到可审计的文献矩阵，不把来源信息错误转化为自信的研究结论。

**文件变更：**

| 操作 | 拟议路径 | 文件内部需包含的内容 |
|---|---|---|
| A | `skills/paper-reading/SKILL.md` | scan/understand/reconstruct 三档；保留原文公式、页码、章节、假设及结论支撑 |
| A | `skills/literature-review/SKILL.md` | 来源选取、检索式、筛选、去重、前后向引用、近年更新和文献定位表 |
| A | `skills/research-novelty/SKILL.md` | 研究问题→最近相关文献→机制重叠→新增结论→新颖性证据；允许 `INSUFFICIENT_EVIDENCE` |
| A | `schemas/paper-record.schema.json` | DOI、首发/卷期年份、期刊、学科、方法、变量、章节、公式、来源锚点 |
| A | `schemas/literature-matrix.schema.json` | 文献×机制/玩家/变量/信息/方法/结论矩阵；每单元支持 `unknown/not_reported` |
| A | `src/emr/core/provenance.py` | `SourceAnchor(file_id, page, equation_id, section, quote_span)` 及来源—主张关联 |
| A | `src/emr/adapters/bibliography.py` | `lookup_doi`, `deduplicate`, `resolve_bibtex`（网络调用可选） |
| A | `templates/research-project/literature-matrix.md` | 论文对照模版：2021—2026 年同领域研究的研究缺口定位 |
| A | `tests/unit/test_paper_record.py` | 发表年份区分、DOI 格式与未知字段处理 |
| A | `tests/unit/test_provenance.py` | 页码/公式定位、来源 ID 存在性、无来源时不得设 `CLAIM_SUPPORTED` |
| A | `tests/integration/test_literature_offline.py` | 使用合成短论文/本地固定元数据完成闭环，不依赖外网 |

**重要逻辑**：

1. PDF 读取后保留真实页码与原文公式文本；提取失败记 `UNREADABLE`，不猜测公式。
2. `citation metadata verified` 与 `claim supports statement` 是不同工件。DOI 验证不能替代对原文实质内容的查核。
3. 多轮检索必须保存检索式、日期、数据库、筛选原因，不能以“无搜索结果”推论“全球首创”。
4. 期刊分区是带年份、体系和类别的元数据，不写成固定期刊等级。
5. 文献中的文件名注释不应覆盖论文真实标题与研究主题。
6. 默认只读本地 PDF；必要时访问外部全文/API 需按权限及版权规则执行。

**验收**：对人工合成的重复 DOI 和错误年份进行去重并保留首发/卷期；不确定字段明确标缺失；文献矩阵中的每个结论有来源定位或 `NOT_VERIFIED`。

**回滚**：删除/撤回新增索引前保留来源数据；任何已生成论文草稿应只取消下游引用，不删除原始研究笔记。

### Phase 3 — 经济模型设计与研究类型路由

**目标**：完成严谨的模型事实契约，把 pAI-Econ 理论谱系转为可检查的输入，而不是生成任意可读段落后立即求解。所有符号表达式须采用**有限运算符白名单的 AST/DSL**或受约束的结构化表示，禁止将不可信 PDF/LLM 文本直接传入 Python `eval`、`exec` 或无安全审计的动态 `sympify` 字符串解析器。

**文件变更：**

| 操作 | 拟议路径 | 内部修改逻辑 |
|---|---|---|
| A | `skills/economic-model-design/SKILL.md` | 从现实问题提炼机制、列明玩家/信息/时间/行动/效用；匹配基准模型与差异 |
| A | `references/economic-model-library/README.md` | 仅引用并索引被批准复用的上游模型知识；标出处与适用域 |
| A | `references/economic-model-library/stackelberg.md` | 策略空间、跟随者反应与领导者最优；无默认唯一均衡假设 |
| A | `references/economic-model-library/platform-hotelling.md` | 双边加入、网络效应、效用和参与约束 |
| A | `references/economic-model-library/principal-agent.md` | Hidden Action/Type；IR/IC、可观察与不可观察信息 |
| A | `schemas/model-spec.schema.json` | 状态/控制变量、玩家、顺序、信息集、约束、量纲和来源；**表达式 AST/DSL 版本、白名单运算符、符号表、域、输入大小限制**，拒绝任意代码片段 |
| A | `src/emr/domain/game.py` | `validate_game_spec`, `check_information_sequence`, `build_best_response_tasks` 的领域规则 |
| M | `src/emr/core/router.py` | 根据 `research_type` 加载 analytical_game/stochastic/empirical/hybrid 分支 |
| A | `tests/unit/test_game_spec.py` | 漏目标函数、错误变量域、行动者与顺序不一致及含危险表达式的模型输入应失败；参数限制缺失可 BLOCKED 而非擅定方向 |
| A | `tests/unit/test_information_sequence.py` | 检测未来状态被前期决策者直接观察的时间逻辑错误 |

**必须实现的模型合理性检查**：

- 策略和参数域是否明确；需求/概率在域内是否有效；变量量纲是否一致。
- 决策可见性与阶段顺序：未来退货信息不可用作当前确定性反馈，除非有可建模的预测信息。
- 模型基准回退：关闭新增机制（例如 替代系数设为 0）时，能否退化到合理的基准模型。**注意退化并不等于必须与原论文同式**。
- 参数外生/内生划分，边界值是否改变模型形式。
- 创新性论述由文献证据驱动，**不能“多一个变量”就自动宣称贡献**。

**验收**：从已知静态 Stackelberg 示例生成完整 `model-spec` 并拒绝缺失信息集、恶意表达式及缺少关键参数域的输入；能把 2025 Omega 的随机供给类问题标为随机序贯博弈而非连续时间 HJB。

**回滚**：模型版本变更时将依赖它的求解、命题和图表标失效（`STALE`），保留原模型快照，不触发全局文献重查。

### Phase 4 — 均衡引擎、比较静态与合同机制（核心数学里程碑）

**目标**：在有定义的模型类别上正确求解和验证，不宣称支持任意非线性博弈。

**文件变更：**

| 操作 | 拟议路径 | 内容与接口 |
|---|---|---|
| A | `skills/game-equilibrium/SKILL.md` | 跟随者→领导者逆向归纳；解析/数值/无法求解分支；要求证据与边界比较 |
| A | `skills/contract-mechanism/SKILL.md` | 佣金、固定费、成本补贴、风险分担、净销售额合同及 IR/IC/协调定义 |
| A | `src/emr/adapters/symbolic_sympy.py` | `differentiate`, `solve_foc`, `simplify_identity`, `substitute`, `hessian`；精确有理数及明确假设；**仅接收已校验的 AST/内部表达式对象**，禁止未经授权解释字符串为 Python 代码 |
| A | `src/emr/adapters/numerical_scipy.py` | `optimize_constrained`, `find_roots`, `evaluate_residuals`, `parameter_grid`；记录容差和初值 |
| A | `src/emr/domain/contract.py` | `verify_individual_rationality`, `verify_incentive_compatibility`, `test_coordination` |
| A | `schemas/equilibrium-result.schema.json` | 均衡对象、策略域、参数条件、最优性证据、多解/边界标记 |
| A | `tests/fixtures/stackelberg_linear/` | 人工推导的可解析实例与标准答案 |
| A | `tests/fixtures/contract_coordination/` | 含参与约束、IR/IC 的小型可解析例子 |
| A | `tests/unit/test_best_response.py` | 最佳反应能正确回代并满足可行域 |
| A | `tests/unit/test_corner_cases.py` | 内点不可行、边界最优、多解、不可行条件 |
| A | `tests/unit/test_contract_conditions.py` | 协调与 Pareto 改进不混淆；合同支付守恒 |
| A | `tests/integration/test_stackelberg_end_to_end.py` | 解析解、回代、一二阶检查及数值交叉验证 |

**拟议逻辑规则**：

1. 对跟随者先求候选驻点，再检查域、凹性、边界及全局最优；必要时枚举多个最佳反应集合。
2. 领导者在跟随者的合法最佳反应上优化，定义多解时的选择规则或报告模糊性。
3. 只有 FOC 但没有充分条件时标 `CANDIDATE_STATIONARY_POINT` 而不是均衡。
4. 有约束且满足适用正则性条件的问题使用 KKT 作为候选必要条件；只有在相应充分条件成立时才能据此认定全局最优。非凸数值优化须报告多初值、残差和局部性；不得用一组数值点证明普遍命题。
5. 比较静态必须返回**符号方向成立的参数域**，无法定号时允许 `SIGN_INDETERMINATE`。
6. 合同协调至少明确“决策匹配集中最优”和“系统利润达到集中最优”的区别；双赢另外检查各方参与约束。
7. 若无闭式解，返回可复现数值求解路径及失败状态，不伪造解析式。

**验收**：至少使用**两类**合成 Stackelberg 测试：(1) 手推闭式解与边界、凹性核对；(2) 能让 follower 的反应**改变 leader 最优决策**的战略反馈案例。一个只让 leader 的利润倍乘而最优价格不变的案例不足以单独覆盖 (2)。另需在合同示例中构造违反 IR 的方案并确认被拒绝；同一参数值使用双重求解路径结果一致（在容差内）。

**回滚**：采用功能开关 `experimental_solver`；出错时切换为仅符号/人工推导报告，不允许“静默采用无验证数值答案”。

### Phase 5 — 数学命题、证明审查与反例搜索

**目标**：将 Theorist Toolbox 的严格标注与系统的符号/数值证据结合；与论文文字润色隔离。

**文件变更：**

| 操作 | 拟议路径 | 内容 |
|---|---|---|
| A | `skills/theorem-verification/SKILL.md` | 构造、审查、反例、失败分类；`OK/GAP/ERROR/UNCLEAR` 分步标记 |
| A | `src/emr/domain/proof.py` | `register_obligation`, `audit_proof_step`, `record_counterexample`, `render_proof_status` |
| A | `schemas/proposition.schema.json` | 严格命题陈述、全称/存在量词、参数域、引用引理、证明版本 |
| A | `schemas/verification-report.schema.json` | 检查范围、判定、开放义务、证据引用、审稿意见严重性 |
| A | `templates/theoretical-paper/proof-appendix.tex` | 带证明编号与 `\unproven{}` 占位的论文附录模板 |
| A | `tests/unit/test_proposition_state.py` | 未证明命题不能变 `PROVED`；被反例推翻的命题需冻结 |
| A | `tests/unit/test_counterexample.py` | 数值反例应满足约束、记录精度并重新回代 |
| A | `tests/integration/test_proof_audit.py` | 对刻意错误的符号结论检测到 ERROR |

**重要规则**：

- `proof sketch accepted` 仅代表证据链完整程度较高，不能晋升 `proved`。
- 反例须核对参数可行域和优化器是否找到真最优；数值求根失败不是定理反例。
- 关键数学结果应执行“构造性检查 + 对抗式检查”，但多 Agent 并行属于可选，避免每个小步骤耗费高成本。
- Lean 4 是高级可选验证；仅对稳定、严格形式化的命题尝试；没有 Lean 环境也能完成标准人类可审查证明。
- 不允许写作模块为消除难看的 `\unproven{}` 而删除证明义务。

**验收**：错误导数符号可以被检测并显示反例；已证明命题在收缩参数域后重新生成验证报告；未证明命题无法被导出为“严格证明”标签。

**回滚**：验证失败不回滚模型本身，而是阻止相应结果进入正式稿并在工件系统标记依赖失效。

### Phase 6 — 随机运营、动态模型及理论复现

**目标**：分开覆盖用户上传的 IJPE 随机需求、Omega 随机供应与 MDE 连续时间动态协调等典型范式。此阶段优先构建可验证的最小模型与复现接口；**不承诺首版通用求解任意 HJB / 微分博弈**。

**文件变更：**

| 操作 | 拟议路径 | 内容 |
|---|---|---|
| A | `skills/stochastic-optimization/SKILL.md` | 随机变量/分布/信息先后/期望利润/库存与风险；动态和随机路径区分 |
| A | `skills/dynamic-optimal-control/SKILL.md` | 连续时间状态、控制、协态、Hamiltonian/HJB 适用前提、初值及横截条件；不与随机优化混同 |
| A | `skills/paper-replication/SKILL.md` | 原文抽取→独立推导→数值复现→差异定位→报告，支持部分复现 |
| A | `src/emr/domain/stochastic.py` | `check_distribution_support`, `validate_information_timing`, `expected_objective` |
| A | `src/emr/domain/dynamic.py` | `validate_state_system`, `check_transversality_requirements`, `build_optimal_control_tasks` 的最小接口；复杂求解器 `[需要进一步确认]` |
| A | `src/emr/domain/replication.py` | `build_replication_manifest`, `compare_results`, `classify_discrepancy` |
| A | `schemas/replication-report.schema.json` | 公式/命题/表格/图分项结果与参数可追溯信息 |
| A | `tests/fixtures/stochastic_supply/` | 人工生成的二点分布/截断分布测试用例；每个参数有明确真值 |
| A | `tests/fixtures/differential_state/` | 可解析线性动态状态方程样例 |
| A | `tests/unit/test_dynamic_timing.py` | 检查状态初值、控制可观察性、终端与横截条件缺失的错误/警告 |
| A | `tests/integration/test_replication_baseline.py` | 符号解/数值图/原始模型假设三段对照 |
| A | `examples/paper-replication/README.md` | 复现样例输入输出与版权约束；不上传受限制 PDF |

**运行方法**：

- 第一层：已知解析解基准 Stackelberg（不使用真实论文版权材料）。
- 第二层：2021 年 MDE 收益分成协调论文（已取得合法论文文本的前提下）复核均衡与协调条件，包括可行边界。
- 第三层：2025 年 Omega 随机供应四情形 `RT/RL/MT/ML`，以原文列示参数为准复核命题及图表。
- 第四层：2024 年 IJPE 库存模型、2025 年 JRCS Hotelling 平台模型、2026 年相关直播模式的扩展测试。**不要求 Phase 6 首次通过所有复杂案例；每例可单独验收并记录阻断原因。**

**随机与动态建模必查**：

- 期望与优化次序 `max E[Π]` vs `E[max Π]` 是否与信息结构吻合。
- 随机分布支撑集、截断、独立性和可积性条件。
- 连续时间动态模型中的状态方程、初值、协态/HJB 使用条件、终端或横截条件；不能把任意含时间指数的模型都称为微分博弈。
- 数值随机试验保存采样方法、随机种子、样本量、置信不确定性及计算环境。

**验收**：在合成模型中确认先决策与后决策的目标不同；对缺失参数或无原文公式的情况返回 `UNREPRODUCIBLE_INPUT`；同输入/版本/种子重新生成相同结果（容差下）。对动态分支，首版只要求可正确核查线性状态方程、最基本的最优控制必要条件与输入完整性；复杂 HJB/随机微分博弈标 `UNSUPPORTED`，禁止假称已求解。

**回滚**：失败案例局部隔离；上游论文记录和模型事实不删除；撤销错误的结果发布状态。

### Phase 7 — 实证计量与理论实证混合研究（独立可选分支）

**目标**：不污染理论研究主路径，满足未来真实直播电商数据、因果识别与理论校准需求。

**文件变更：**

| 操作 | 拟议路径 | 内容 |
|---|---|---|
| A | `skills/econometric-analysis/SKILL.md` | 研究识别、数据清理、内生性、DID/IV/Panel 等按问题选择 |
| A | `src/emr/domain/econometrics.py` | `validate_design`, `collect_estimand`, `check_identification_assumptions` 等接口草案 |
| A | `templates/empirical-paper/main.tex` | 引言、数据、识别策略、结果、机制、稳健性、讨论等可配置章节 |
| A | `tests/unit/test_empirical_claims.py` | 关联/预测不能自动写作因果结论；缺失识别假设应警告 |
| A | `tests/fixtures/synthetic_panel/` | 不包含隐私的合成面板/截面测试数据 |

**策略**：Auto-Empirical Research Skills 仅作流程参考；先实现最小证据管理，后续根据数据类型引入 Statsmodels/linearmodels/R/Stata 接口 `[需要进一步确认]`。严禁将训练预测性能直接写成经济因果效应。

**验收**：没有实证数据时理论研究照常可用；实证分支能拒绝未定义 `estimand`/识别假设的因果论断。

**回滚**：可独立禁用整个 `empirical` extra，不影响模型及写作模块。

### Phase 8 — 论文写作、引文、排版、投稿前检查

**目标**：将已验证的研究工件转为有期刊适配性的英文或中文论文稿件，不允许润色阶段更改数学事实。

**文件变更：**

| 操作 | 拟议路径 | 内容 |
|---|---|---|
| A | `skills/academic-writing/SKILL.md` | 论证优先级、贡献表述、章节一致性、命题解释；禁止添加无法追溯的结果 |
| A | `skills/citation-audit/SKILL.md` | DOI/作者/年/期刊元数据检查及论断—来源支持检查 |
| A | `skills/submission-review/SKILL.md` | 匿名化、图表、补充材料、期刊指南、模拟审稿、回复意见 |
| A | `templates/theoretical-paper/main.tex` | 默认可调章节及 proof appendix 接口，不锁死章节数 |
| A | `templates/theoretical-paper/references.bib` | 模板占位，不添加虚构引文 |
| A | `references/journal-profiles/README.md` | Omega、IJPE、JRCS、ECR 等目标期刊的配置机制；规则须以官网最新说明核对 |
| A | `src/emr/domain/manuscript.py` | `check_claim_evidence`, `collect_verified_results`, `render_section_outline` |
| A | `tests/unit/test_citation_integrity.py` | 未验证条目、重复 DOI、引用键缺失、被撤稿声明警报 |
| A | `tests/unit/test_manuscript_consistency.py` | 同一符号定义冲突、表图未引用、定理状态与论文表述不符 |
| A | `tests/integration/test_latex_compile.py` | 具备 TeX 时编译最小模板，不具备则标注 SKIP 而非 PASS |

**写作默认模板（分析型运营管理论文，可配置）**：

1. Introduction — 现实矛盾、研究问题、核心发现与贡献。
2. Literature Review — 研究流派、最接近研究、与本文差异。
3. Model Setup — 场景、博弈顺序、假设、效用、需求与利润。
4. Equilibrium Analysis — 逐模式求解、阈值、比较静态。
5. Strategy/Contract Comparison — 经济机制、协调、福利及参与约束。
6. Numerical Analysis / Extensions — 按目标期刊可调整先后或拆分。
7. Conclusions — 理论/管理启示、限制与未来研究。
Appendices — 完整证明与计算细节。

**禁止行为**：引用不真实 DOI、杜撰期刊分区、把证明草图叫作严格证明、把仿真区域称为普遍定理、用语言润色覆盖模型错误、未经确认进行外部查重或向第三方上传未公开稿件。

**验收**：固定示例稿中故意放置一个无证据断言和一个未验证数学命题，投稿检查必须拦截；可在无网络条件下执行本地格式与一致性检查；线上期刊规则校验属于另一个可选步骤。

**回滚**：独立保留每版 `.tex`、`.bib` 与验证报告；若论文正文滞后于模型新版本，标 `STALE` 并撤回“可投稿”状态。

### Phase 9 — CI、安全、可维护性与发布准备

**目标**：研发流程稳定、可追溯、减少重复开销，且对公开项目与数据安全友好。

**文件变更：**

| 操作 | 拟议路径 | 内容 |
|---|---|---|
| M | `.github/workflows/validate.yml` | 增量 Lint、Schema、测试分层、依赖安全检查；不从 PR 执行不受信任任意脚本 |
| A | `src/emr/core/cache.py` | 内容寻址缓存；版本化缓存键与依赖失效图 |
| A | `tests/integration/test_incremental_execution.py` | 局部模型修改只重跑相应下游，已验证文献任务不重跑 |
| A | `tests/integration/test_security_boundaries.py` | PDF 注入、路径穿越、外部脚本、私有路径泄露模拟 |
| A | `docs/OPERATIONS.md` | 安装、运行、故障排查、版本升级与清理工件 |
| A | `docs/RELEASE_CRITERIA.md` | alpha/beta/stable 验收指标和已知限制 |
| A | `docs/CHANGELOG.md` | 结构/接口/验证逻辑的演进记录 |
| A | `docs/SECURITY.md` | 密钥与私有稿件、依赖/第三方脚本处理原则 |

**阶段测试建议**：

- `static`：Skill frontmatter、YAML/JSON Schema、受限路径、license 清单。
- `unit`：无外部模型、无需网络、目标秒级运行。
- `integration-offline`：短例子完整推导、回代、证明状态和稿件一致性。
- `integration-online`：需显式凭据、权限和测试授权，CI 默认关闭。
- `long-running`：复杂随机/动态/形式化证明，手动按任务执行，不设为每次提交必跑。

**发布要求**：至少具备可重现的安装说明、锁定版本、1 个经验证的理论案例、1 个“失败应当阻断”的反例、明确局限、第三方 notices。不得以全部上游测试通过替代本仓集成验收。

**回滚**：保留上一个可工作版本与锁定依赖；出现核心数学回归优先禁用受影响模块、恢复已验证产物映射，然后定位错误，严禁默默篡改已发布论文结果。

---
## 5. 风险评估、兼容性矩阵与应对

风险评级按 `发生可能性 (L/M/H) × 影响 (L/M/H)` 的定性组合评估，**不是测试测量值**。

| ID | 风险及连锁反应 | 等级 | 预防/验证 | 失败处置 |
|---|---|---|---|---|
| R01 | 空仓库误当已有架构，设计建立在不存在的 API 上 | H | 所有路径标 A/M；Phase 1 落地后再复查 | 停止实现，更新 RFC 与契约 |
| R02 | 上游 Skill `name` 重名、frontmatter 冲突，路由不稳定 | H | Registry 唯一性/循环依赖测试 | 重命名本仓技能，建立别名映射 |
| R03 | solving-model 依赖 Oracle CLI、外部 `~/.claude/preferences`，脱离原环境失败 | H | 静态扫描绝对路径；离线冒烟测试 | 删除硬依赖、提供本地默认规范；外部审计降级 |
| R04 | pAI-Econ 证明草图 Gate 被误认为完整证明 | H | 状态机将 SKETCH 与 PROVED 隔离 | 阻断论文定理引用，补完整证明 |
| R05 | 最优条件只找到驻点，忽略 KKT/边界导致均衡错误 | H | 边界测试、残差、全局比较、强凹性与多初值 | 调整命题条件，撤回错误结论 |
| R06 | 数值网格/仿真被误写为一般性数学证明 | H | 文稿状态检查，未证明命题不标定理 | 更改为数值观察或补严格证明 |
| R07 | 模型时序错误，例如提前观察未来退货 | H | 信息集/可观测性校验和人工审查 | 修改博弈树，所有下游均衡作废 |
| R08 | DOI 正确但引用并不支持所写结论 | H | 元数据与实质支持两级审查，保留页码 | 修正文稿、替换引文、标未证实 |
| R09 | 论文复制/公开第三方 PDF、代码未经授权 | H | 许可清单、私有数据路径、发布扫描 | 停止发布、移除未授权内容并审查历史 |
| R10 | API Keys、未公开论文或企业数据被发往外部服务 | H | 默认本地、外传批准、日志脱敏 | 立刻禁用连接器、轮换密钥、调查暴露范围 |
| R11 | 上游 HEAD 更新造成接口或 prompt 漂移 | M | 引用 SHA、锁定依赖、独立适配器 | 回退上游快照，隔离故障 |
| R12 | AI 多代理并行审查耗费大量额度并给出相同错误 | M | 仅关键定理升级双重审查，独立验证路径 | 采用确定性计算/人工数学审查 |
| R13 | 引入 R/Stata/Lean/LaTeX 造成安装复杂与平台差异 | M | extras 可选、离线最小安装、跨环境测试 | 关闭相关插件，不阻断核心路径 |
| R14 | `pytest` 测试“通过”但只覆盖提示词结构而非数学正确性 | H | 真值样例、反例样例与论文级验收并行 | 禁止发布“数学已验证”声明 |
| R15 | 参数扫描成本失控、大规模作图占用计算资源 | M | 参数预算、最大点数、缓存、显式高成本批准 | 停止单节点，保留已完成工件 |
| R16 | 研究范式错路由，实证研究被强制走理论博弈 | M | 意图/研究类型交叉测试；人工覆盖机制 | 局部重规划，保留文献成果 |
| R17 | 模型变化后论文未同步、结论与公式错配 | H | 输入哈希、依赖链、稿件一致性检查 | 标为 STALE，重新生成受影响节 |
| R18 | 论文模板过度统一，期刊要求不匹配 | M | 目标期刊官网版本化规则，模板切换测试 | 恢复通用模板，单期刊覆盖 |
| R19 | 验证过程多轮全量重跑耗时高 | M | 依赖图+内容哈希+跳过无关模块 | 重试失败节点及依赖受影响子图 |
| R20 | 学术诚信：未知结论、假设或数据被 AI 编造 | H | 引文、证明、参数三类 provenance 强制检查 | 退回待确认、禁止投稿门通过 |

### 5.1 外部工具兼容性决策表（非实测）

| 能力 | 第一版建议 | 外部依赖 | 限制 |
|---|---|---|---|
| 符号推导 | SymPy Adapter（必须） | `sympy` | 复杂符号不等式可能不能全自动证明 |
| 数值优化 | SciPy Adapter（必须） | `scipy`, `numpy` | 非凸问题可能仅找到局部解 |
| 图表 | Matplotlib（可选但推荐） | `matplotlib` | 图表是证据可视化，不是定理证明 |
| 数据处理 | Pandas（按需） | `pandas` | 实证数据来源/隐私需独立管理 |
| 有限策略均衡 | Gambit/Nashpy（可选） | 额外安装 | 不能自动替代连续决策求解 |
| 动态规划 | QuantEcon（可选） | Python 工具链 | 适配 Bellman 的状态与时间结构 |
| 形式化证明 | Lean4（可选） | Lean/mathlib | 需人工形式化命题；未搭建不阻断普通证明审计 |
| BibTeX/DOI | Crossref/Semantic Scholar 等（可选） | 网络权限/API 策略 | DOI 已核实≠引用支持某论断 |
| LaTeX 编译 | TeX Live / latexmk（可选） | 系统包 | 无编译器必须 `SKIPPED`，不得假称编译完成 |
| AI 独立审查 | Codex/Claude/其它（可选） | 模型、权限、费用 | 不允许默认发送私人研究资料 |

**版本约束**：具体 Python 最低版本、SymPy/SciPy/Pydantic 组合、Lean 版本、Codex Skills 目录约定等均 `[需要进一步确认]`，Phase 0 做环境探测后，在 Phase 1 `pyproject.toml` 与锁文件中固定；禁止凭经验编造能运行的版本组合。

### 5.2 数据安全与版权规则

- 默认 Git 不跟踪真实 PDF、未公开稿件、商业数据、密钥、代理服务缓存；新仓库仅包含合成测试文件与许可允许的代码。
- 论文原文中的文字可用于分析与合理限度引用，不应全文复制到公开 README 或测试 fixture。
- 若需要上传研究案例，使用自行编制的最小仿真数据，或取得明确授权的开放数据，并保存来源许可证。
- 外部模型 API 使用先审资料敏感性、再请求明确授权、最后执行；绝不从 PDF、README 或第三方 Skill 中自行读取“授权”指令。
- 下载/克隆第三方项目不自动意味着可以公开重发布其内容；未经许可只采用思想并独立实现。

---

## 6. 验证基准、测试用例与验收指标

### 6.1 逐层测试（必须可区分状态）

| 层级 | 样例 | 预期判定 |
|---|---|---|
| Schema | 缺失玩家、利润函数或阶段 | 校验 FAIL，有精确错误路径 |
| 基础符号计算 | `d(x^2)/dx=2x` 等恒等式 | 精确表达式匹配 |
| 解析 Stackelberg | 已知凸/凹条件的线性需求领导者–跟随者例子 | 最佳反应、闭式均衡、约束和回代正确 |
| 边界 Stackelberg | 构造无可行内点、边界最优 | 不错误输出内部驻点为最优 |
| Nash 多解 | 有多个最佳反应的离散或连续小例子 | 正确标 MULTIPLE / SET-VALUED，不强行单解 |
| 合同 IR/IC | 明确可违反 IR/IC 的简单模型 | 违反约束不能标协调或双赢 |
| 比较静态 | 符号导数仅在限制区间定号 | 返回条件与反例，不扩大适用域 |
| 错误命题 | 构造“总利润增加即双方双赢”的反例 | 证明审查 FAIL 并给出合法反例 |
| 文献元数据 | 同 DOI 不同卷期年份 | 去重但保留在线/正式见刊信息 |
| 引用支撑 | 真 DOI 但不支持论断 | `METADATA_VERIFIED` 且 `CLAIM_UNSUPPORTED` |
| 随机供给 | 决策前后观察状态互换 | 不同信息结构求值不同并标明原因 |
| 论文复现 | 原文图/表缺少参数 | `UNREPRODUCIBLE_INPUT`，不伪造参数 |
| 写作一致性 | 更改模型中的佣金含义 | 依赖的正文标 STALE |
| 隐私安全 | 恶意 PDF 命令/路径遍历 | 拒绝执行/越权访问 |
| 增量执行 | 只改论文润色规则 | 不重新求解数学模型 |

### 6.2 推荐一个可手算的 Stackelberg 基准

**以下为计划指定的合成测试问题，不是从某篇论文原文提取：**

零售商为领导者先选零售价 \(p\)，服务商/主播随后选努力 \(e\)。为避免跟随者努力与领导者定价完全脱钩，使用**价格影响努力激励**的合成模型，以下系数和结果仅用于测试，不来自原论文：

\[
\Pi_F(e\mid p)=a(A-bp)e-\frac{c}{2}e^2,
\qquad e\geq0;
\]

\[
\Pi_L(p,e)=(p-w)(A-bp+\gamma e),
\qquad p\in[w,A/b].
\]

设 \(a,b,c,A>0,\gamma\geq0,w\geq0,A>bw\)，且最优反应以 \(p\) 为条件。此时严格凹的跟随者问题给出

\[
e_F^*(p)=\frac{a(A-bp)}{c};
\]

代入领导者利润并求解，在上述范围内得到唯一内部价格解及努力：

\[
p^*=\frac{A+bw}{2b},\qquad
 e^*=\frac{a(A-bw)}{2c}.
\]

这些结果可用手算独立验收，同时单独设计 \(p>A/b\)、无效参数及边界候选等**故意失败**的测试，确保路由器不会把非法驻点当成均衡。该案例不作为具有经济创新性的论文研究结果；真实业务模型须另行设定更加可信的收益分配与行为机制。

另增两个故意失败的测试：

1. `e<0` 的候选解应被可行域拒绝。
2. 将佣金参与约束移除后“协调”结论可能不再双方接受，合同模块应分开报告系统效率与个体利益。

**补充战略反馈回归例（与上方基础例不同）**：令跟随者利润 `Π_F=a·p·e−(c/2)e²`，领导者利润 `Π_L=(p−w)(A−bp+γe)`，约束 `p∈[w,A/b]`、`e≥0`。当 `A=10,b=1,w=2,a=c=1,γ=1/5` 时，最优跟随者努力为 `e^*(p)=p`，领导者最优价格为 `p^*=29/4`、努力 `e^*=29/4`，且领导者目标二阶导数 `−8/5<0`；若 `γ=0` 则价格为 `6`。这可检验求解器确实将领导者的最优决策与跟随者反应联系起来。该例仅在上述参数与域内充当固定测试真值；**不代表任意参数下都具有内部最优解**。

### 6.3 论文级验收阶梯

- **A0 静态技能加载**：Skill frontmatter、引用路径、Schema 能读取，外部依赖可声明未安装。
- **A1 合成解析模型**：至少一个有闭式解 Stackelberg + 一个错误命题被识别；所有证据有报告。
- **A2 论文级解析复现**：用户已有 2021 年 MDE 论文中选定的均衡/协调公式独立复核，原文定位、可行性边界可追溯。
- **A3 论文级随机模型**：用户已有 2025 年 Omega 供应风险研究至少两个模式的关键结果复现，再扩展到四模式。
- **A4 跨范式测试**：JRCS 双边平台/Hotelling 与 IJPE 随机库存类型至少各一个独立案例；若因材料不足明确标部分完成。
- **A5 论文产出检查**：根据真实已验证结果生成稿件结构、有效引用与附录，格式对照目标期刊。

**不能将 A0 通过等同于 A3；不能以“AI 看过且无异议”代替 A2 的推导证据。**

### 6.4 质量门标准

| Gate | 必要输入 | 允许通过的证据 | 拒绝情况 |
|---|---|---|---|
| G1 文献真实性 | PDF/DOI/元数据 | 可靠来源及定位 | 不可证实引用伪装真实 |
| G2 研究定位 | 近期相近文献表 | 实质机制差异及局限陈述 | 简单添加变量宣称首创 |
| G3 模型一致性 | model-spec | 时序/信息/参数/维度自洽 | 漏目标函数或未来信息穿越 |
| G4 数学验证 | equilibrium + proofs | 严格推导与恰当边界结论 | 只有 FOC/数值网格却称全局成立 |
| G5 计算复现 | 代码、版本、参数 | 实际运行数据与论文报告一致 | 未运行却宣称复现；选择性遗漏反例 |
| G6 投稿审查 | manuscript + citation | 论断证据、章节、图表、目标格式一致 | 引文不支持结论、结果状态过期 |

**研究范式适配规则**：`G4` 面向理论命题/均衡；对纯实证研究，以识别假设、估计量和推断审查的 `G4E` 代替，不能要求其证明不存在的博弈定理。`G5` 对包含数值/实证/图表结论的工作强制核验；对真正无计算结果的纯理论文章，需记录 `NOT_APPLICABLE` 与依据，**不能把跳过称为 PASS**。混合研究两类门均适用。

**失败处理的状态规则**：

- `PASS`：符合本 Gate 严格定义的适用范围。
- `CONDITIONAL`：仅非关键事项待补；重要数学命题不得以此绕过 G4。
- `BLOCKED`：需要信息或环境，不能得出通过/失败。
- `NOT_APPLICABLE`：研究设计经确认不适用该 Gate；保留理由及批准记录，不计为 PASS。
- `FAIL`：已经有反例、矛盾或严重缺口。

任何新证据可使之前 `PASS` 被撤回；记录撤回原因和影响依赖，不能删除审查历史。

---

## 7. 依赖关系、增量执行与成本控制

### 7.1 工件 DAG 示意

```text
paper-source ─→ paper-record ─→ literature-matrix ─→ novelty-report
                                                  │
research-question ────────────────────────────────┘
            ↓
       approved-model-spec
            ↓
      equilibrium-result ──→ proposition-set ──→ proof-report
            │                      │                  │
            └──────────────────────┴──────→ replication-report
                                             │
       verified-citations ────────────────────┤
                                             ↓
                                         manuscript
                                             ↓
                                      submission-audit
```

上述 DAG 用于依赖失效分析，不意味着研究过程必须从文献开始：直接提供 `approved-model-spec` 时可跳过不相关步骤。

### 7.2 缓存与重试规范

- 缓存键建议包括 `sha256(inputs + schema_version + skill_version + code_commit + environment_fingerprint + parameter_config)`。
- 网络检索附日期和来源快照；文献检索结果有时效性，不允许永久沿用而不提示。
- 修改 `model-spec` 触发相应 `equilibrium-result`, `proof-report`, `replication-report`, `manuscript` 失效，不触发无关文献 PDF 重解析；**最小失效/状态标记在 Phase 1 `artifacts.py` 就应可用**，Phase 9 的 `cache.py` 仅优化复用和性能。
- 只修改文稿语言风格时不触发均衡/证明/数值重跑。
- 执行脚本需幂等；每个节点写自己的产物目录，新实验不覆盖最后一次已批准版本。
- 每次失败保存异常、输入哈希、调用来源、日志和已有产物；重试失败节点及依赖子图，**不得默认从 Stage 1 全量重启**。
- 超时/费用预算默认保护；理论模型的关键错误不能因为“额度不足”被自动忽略。

### 7.3 责任边界与人工审核

| 角色 | 允许写入 | 不允许做什么 |
|---|---|---|
| literature | paper records、检索日志、文献矩阵 | 直接修改经济模型结论 |
| model-design | model-spec 新版本 | 擅自判定命题已证明 |
| solver | 均衡候选/数学计算工件 | 直接把驻点写成正式论文定理 |
| proof-auditor | 验证报告和反例 | 悄悄改公式以符合预期 |
| replication | 复现日志、数值表图 | 重写原始论文数据以制造一致 |
| manuscript | 稿件正文与图表引用 | 改动已批准模型、参数或计算结果 |
| submission-audit | 审查报告 | 未授权正式投稿或发送未公开论文 |

---

## 8. 后续阶段的变更管理与回滚预案

### 8.1 开发准入条件

- 当前用户仅授权本 RFC **同一文件的创建与审计纠错**；以后每次 Phase 0B 或实际工程执行仍须用户批准**明确的写入范围**。Phase 0A 只读核查可先行。
- 任务实施前核对目标仓库 HEAD、目录、已存在文件、相应上游 SHA 与许可证；本计划中的拟议路径不能当作事实。
- 若发现目标仓库已不为空，**优先做真实差异审查**，本 RFC 中的 `A` 应重新分类为 `A/M/skip`，不能覆盖现有内容。
- 每个开发任务有文件列表、成功标准、测试命令、影响范围、回滚办法。
- 未来若允许 Git 工作流，任何 PR/Commit 均应在单独授权后创建；分支名/PR 标题仅是建议，不属于当前计划执行。

### 8.2 里程碑与后续变更批次

| 里程碑 | 建议批次 | 核心交付 | 基线验收 |
|---|---|---|---|
| M0 | 来源与许可证 | Sources、环境矩阵 | 无未知复制许可 |
| M1 | 仓库基础 | 入口、注册、Schema、静态测试 | A0 |
| M2 | 文献与模型 | PDF/文献矩阵 + 模型事实 | G1—G3 |
| M3 | 数学核心 | 均衡、合同、命题审查 | A1 / G4 |
| M4 | 理论复现 | MDE 基准、Omega 随机案例 | A2—A3 / G5 |
| M5 | 写作与投稿 | LaTeX、引用、审稿 | A5 / G6 |
| M6 | 扩展 | 实证、Lean、Gambit、动态数值 | 按各分支独立验收 |

这里的 Phase 编号代表细分实施活动，Milestone 代表面向用户的可用能力。允许延后非核心分支，不要求一次性完成所有内容。

### 8.3 回滚原则

1. **源文件**：后续实施使用版本化更新与测试；回滚应恢复上一个已验证版本，而不是仅撤销最近一个文件却保留不兼容依赖。
2. **科研结果**：原始来源及旧版本证明永久留审计轨迹；结果失效用状态表示，不直接销毁数据。
3. **依赖**：外部服务故障降级到本地或标不可用，不能伪造结果。
4. **Schema**：不兼容字段更名必须增加版本和迁移器，保留旧版本读取能力；迁移测试通过前不删除旧 Schema。
5. **论文**：模型或引用被修正后重新生成受影响章节与附录；不能继续发布过期稿件。
6. **数据**：私有数据不进入公开仓库；回滚不能破坏私有数据原件。

### 8.4 删除与替换清单（谨慎条件触发）

由于当前目标仓库为空，**不存在应删除的现有文件**。以下是未来可能替换的占位，不预先安排实际删除：

- `skills/*` 若早期整库复制了重复上游技能，应先确认是否有被本仓调用，再退役未使用的重复模块；没有依赖图证据不得删除。
- 废弃 schema 按版本迁移，先标 deprecated 并提供迁移器，再在未来破坏性版本移除。
- 未通过安全/许可证审查的第三方文件不能进入正式仓库；若已经错误加入，后续需检查 Git 历史保留与合法处置，单纯删除 HEAD 文件不一定消除已公开内容。

---

## 9. 未决问题与必须确认的决策

以下事项不应由实施者擅自猜测：

| ID | 待确认事项 | 当前状态 | 阻断范围 |
|---|---|---|---|
| Q01 | GitHub 是否已收到本计划文件，后续文档纠错范围是什么？ | **已确认**：初始上传 Commit `44d0d3f7…`；当前仅允许本文件审计修订，不代表后续 Phase 授权 | 非计划文档写入均不得执行 |
| Q02 | 本仓自有代码采用 MIT、Apache-2.0 还是其它许可证？ | `[需要进一步确认]` | `LICENSE` 与复用说明 |
| Q03 | 是否允许未来公开衍生第三方 Skills，是否涉及商业用途？ | `[需要进一步确认]` | CC BY-NC 内容复制、缺许可模块 |
| Q04 | 首选运行平台是 Codex CLI、桌面 Codex、ChatGPT Work、Claude 还是本地 Python？ | `[需要进一步确认]` | Skill 目录与执行适配 |
| Q05 | Python/TeX/GitHub Actions 环境及可用费用预算？ | `[需要进一步确认]` | lock file、CI、外部验证 |
| Q06 | 是否接入 Zotero、Crossref/Semantic Scholar、CNKI、企业数据？ | `[需要进一步确认]` | 文献插件和数据治理 |
| Q07 | 论文与数据是否允许交第三方 API 处理？ | 默认否；需要明确授权 | 外部 AI 审核与联网操作 |
| Q08 | 首个真正复现样例采用 2021 MDE 还是最简合成 Stackelberg？ | 建议先合成，再 MDE | 数学模块验收 |
| Q09 | 研究输出是否中英双语，以及默认英文期刊模板选择？ | 建议核心数据语言无关；模板可切换 | 文稿模块 |
| Q10 | 允许何种数据及代码在公开仓库展示？ | 默认合成案例/许可证允许内容 | 论文级 fixture |

---

## 10. 建议执行顺序与最小可用版本（MVP）

### 10.1 为什么不一开始整合所有 Skill

当前最具价值的风险不是“有没有足够多的 Skill”，而是**能否将真实模型正确还原成数学事实，再证明与复现**。一次性引入数十个技能会放大目录冲突、权限、许可及测试成本。因此建议：

- **MVP-1**：先完成 Phase 0A 只读检查，0B 审计文档落地经授权后完成，再执行 Phase 1；入口可加载，研究工件可校验，无外部模型强依赖。
- **MVP-2**：完成 Phase 2—3，能精读 PDF、形成文献矩阵与完整模型事实。
- **MVP-3**：完成 Phase 4—5，一个小型 Stackelberg + IR/IC 测试 + 一个可自动发现的错误命题。
- **MVP-4**：完成 Phase 6 部分，将 MDE、Omega 分项复现，并生成残差及差异报告。
- **MVP-5**：完成 Phase 8 与 Phase 9 的核心能力，输出引用和命题状态一致的 LaTeX 稿件与投稿前审查报告。
- **Post-MVP**：Phase 7 的深度实证、Lean 4、Gambit/Nashpy、动态最优控制与高级论文自动制图。

### 10.2 最终质量定义

本仓第一版“可用”意味着：

1. 能明确区分已核实内容、假设、数学证明与数值说明。
2. 能对至少一个经管理论基准模型从定义到解析均衡进行独立推导与回代。
3. 能检查并拒绝不满足可行域/IR/IC 的候选结果。
4. 能对模型版本变化标记下游失效，避免重复跑已验证的无关任务。
5. 能生成结构规范的理论论文材料包，并保持引用、符号和命题状态一致。
6. 对无法解决的命题诚实报告 `UNRESOLVED`，不作强保证。

**本项目不以 Skills 数量、模型调用次数或生成篇幅为主要质量指标；以可复查研究事实、正确的数学证据和实际科研效率为核心指标。**

---

## 11. 原始来源与审计链接

本 RFC 主要基于以下 GitHub 仓库当次可访问文件与用户已上传研究论文的方向需求；没有通过软件运行验证所有上游实现。

- pAI-Econ-codex：<https://github.com/Cavaradossi/pAI-Econ-codex>；重点 `SKILL.md`、`prompts/gate-04-proof-integrity.md`、`prompts/07b-numerical-simulation.md`、`model_library/`、`scripts/forward_test_demo.py`、`LICENSE`。
- Theorist Toolbox：<https://github.com/morankor/theorist-toolbox>；重点 `codex/.agents/skills/codex-math/SKILL.md`、`codex/.agents/skills/co-math-init/SKILL.md`、`LICENSE`。
- solving-model：<https://github.com/amatray/claude-skills-public/tree/main/skills/solving-model>；重点 `SKILL.md`、`references/phase-1-setup.md` … `phase-5-documentation.md`。
- paper-reading-skill：<https://github.com/kingslayer-bot/paper-reading-skill>；重点 `SKILL.md`、`scripts/reading_note_quality.py`。
- MGMT-Paper-Skills：<https://github.com/HaonanAlex/MGMT-Paper-Skills>；重点 `mgmt-paper-manuscript-package/SKILL.md`、`mgmt-paper-reviewer-simulation/SKILL.md`。
- research-paper-lifecycle-skills：<https://github.com/ShaishavMaisuria/research-paper-lifecycle-skills>；重点 `skills/verify-citations/SKILL.md`、`skills/verify-results/SKILL.md`、`skills/preflight-check/SKILL.md`。
- Scientific Agent Skills：<https://github.com/K-Dense-AI/scientific-agent-skills>；重点 `skills/literature-review/SKILL.md`、`skills/sympy/SKILL.md`。
- agent-research-skills：<https://github.com/lingzhi227/agent-research-skills>；重点 `skills/novelty-assessment/SKILL.md`、`skills/citation-management/SKILL.md`。
- Economics Writing Skills：<https://github.com/juliaError/econ-TopJournal-writing-Skill>；重点 `skills/econ-write/SKILL.md` 与分层许可证。

**重要审计限定**：文献研究主题依据本对话中用户已上传的 2021—2026 年运营管理论文及既有讨论；本 RFC 不声称本轮对这些 PDF 重新进行逐页数学验证，也未以真实论文数据跑过复现程序。涉及细节的正确性需在 Phase 2/Phase 6 正式执行时重新核对。

---

## 12. 全量静态审查记录（不等于软件测试）

### 12.1 2026-10-12 第二轮独立审计（v0.3）

- **核实仓库**：初始空仓库叙述已修为“目前仅存在 `MODIFICATION_PLAN.md`”；GitHub Contents API 读取确认根目录只有该文件，三套核心上游的 HEAD 与 v0.2 计划记录一致。文档中的 Commit SHA 用作**审查开始时的历史基线**，不应声称自动等于以后 HEAD。
- **修正边界矛盾**：Phase 0 分为 `0A` 只读核查、`0B` 审计文档落地。后者虽不写业务代码，但也是 GitHub 写入，必须与 0A 区分并按授权执行。
- **修正状态契约**：新增独立工件生命周期及 `STALE`；增加 `UNSUPPORTED` 能力状态与 `UNREADABLE`/`NOT_VERIFIED` 的所属分类，避免代码阶段因不一致枚举而失效。
- **修正时序依赖**：Phase 1 增加最小工件依赖失效机制，Phase 9 才引入缓存性能优化；避免 Phase 3—8 使用尚未实现的失效能力。
- **修正输入安全**：新增模型表达式的 AST/DSL 白名单契约，禁止 PDF/LLM 生成的未经审查字符串直接触发 Python 解释器。
- **加强数学回归**：旧合成 Stackelberg 案例公式经独立符号复核属实，但 `p^*` 不随 `γ` 变化；新增独立的战略反馈案例，检验改变努力激励确实改变领导者最优价格。
- **质量门分支**：增加纯实证 `G4E` 和无计算研究 `NOT_APPLICABLE`，防止把理论证明 Gate 强加于所有研究范式。
- **格式与未决问题**：再次核对全篇围栏、标题、计划路径、上游快照和许可证限定；保留真实未解的环境/合规项目，不以“无发现错误”代替上线验收。
- **修正现状表述**：将第 1 节和 Phase 1 的“空仓库”措辞更正为“只有规划文件、尚无业务代码”，避免未来在已有计划文件上重复创建。
- **审计边界**：尚未运行上游第三方 Skills、集成代码或真实论文级复现；“本计划经审查”只表示文档层面与已核查 GitHub 信息相符，不保证未来实现无错误。


- 审查维度：目标仓库基线、上游链接和版本、目录树与逐 Phase 路径一致性、模型状态枚举、数学基准真值、阶段依赖、数据与引用审计、许可/敏感数据、风险与回滚、远程上传授权。
- v0.2 静态修正记录：补齐总目录树中的阶段新增路径；分离求解方法和求解状态；修改可手算 Stackelberg 测试以体现价格影响努力；增加动态最优控制分支的最小职责与测试。**v0.3 的新修正见 12.1**。
- 保留限制：没有执行第三方 Skill、计算库、CI、TeX 编译和真实论文复现，也没有检查所有上游子文件；不能宣称不存在任何未知缺陷。高风险与待确认条目仍需在各 Phase 前逐项复核。
- 文档自身验收：Markdown 格式、代码围栏配对、所有分阶段拟议路径可在总目录树中找到、所有未经实施事项仍为未来态；上传后远程 SHA 与读回正文另行验证。

## 13. 本轮交付确认（Planning Only）

- **已做**：GitHub 只读核对目标仓库与部分上游 Skill/LICENSE；已在先前获批范围内创建初始 `MODIFICATION_PLAN.md`，本轮仅审计与修订同一份计划文档。
- **尚未实施的工程内容**：业务代码和配置修改、PR、分支操作、第三方 Skill 克隆、依赖安装及软件运行测试。本文的上传仅属于经授权的规划文件写入。
- **当前文件**：`/mnt/data/MODIFICATION_PLAN.md`（本地副本）；GitHub 路径：`Vexushi1/economics-management-research/MODIFICATION_PLAN.md`，初始上传已读回成功。
- **文档修订范围**：仅本计划的纠错及审计说明；所有其它文件、分支、PR、业务代码及 Phase 0B 写入仍未执行。
- **下一步建议**：可以开展 Phase 0A 只读来源和环境核查；0B 文档提交与其它工程变更必须按各阶段授权执行。
