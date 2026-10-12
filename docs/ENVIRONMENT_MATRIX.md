# ENVIRONMENT_MATRIX.md — 运行环境需求、版本依据与可用性矩阵

> Phase 0B / 2026-10-12 / 只读环境与上游文件审计。基准：`MODIFICATION_PLAN.md` v0.3。  
> **不代表已在用户的 Codex/本地环境中安装或运行。** 当前可以访问 GitHub 连接器并写入文档，与将来真正运行 Python、TeX、浏览器或 Codex CLI 的机器并不是同一执行环境。未观察到的环境项使用 `UNKNOWN` 和 `[需要进一步确认]`，不可自动归为可用。

## 1. 三种必须分开的环境

| ID | 环境 | 本次能证明什么 | 无法直接证明什么 | 当前状态 |
|---|---|---|---|---|
| E01 | 当前 ChatGPT 会话 + 已连接 GitHub 工具 | 已通过 GitHub API 只读核对源码、创建 Markdown 文件 | 目标机器的 Python/Node/TeX/Codex 工具链、shell 权限、私有数据存放位置 | `OBSERVED_API_ONLY` |
| E02 | 用户将来使用的 Codex CLI / IDE / 桌面或云环境 | 公开上游具有 Codex 版 `SKILL.md` 与 `.agents/` 示例 | 用户实际版本、Skill 发现规则、custom agents/subagents 是否允许、读写沙盒、网络可用性 | `UNKNOWN` `[需要进一步确认]` |
| E03 | 用户将来使用的本地/CI 数值运行机 | 代码规划需要符号与数值工具、模型可重复测试 | OS、CPU/RAM、Python、依赖解析、Tex 发行版、CI 权限、联网/费用/凭据 | `UNKNOWN` `[需要进一步确认]` |

**研究工作流基线决策（拟议、非已验收）**：不把云浏览器、Oracle CLI、付费 LLM、原始 PDF 抓取器、TeX 编译器设为整个研究系统的硬依赖。先以无需联网的只读路由、Schema 校验和简单数学单测作为将来的最低能力；理论求解分支再安装数学依赖。

## 2. 语言/工具/系统版本矩阵

| 组件 | 上游文件中的证据或设计需求 | 建议角色 | 是否确认目标已安装 | 后续验证/阻断 |
|---|---|---|---|---|
| Python | Theorist `skills/second-brain/package/pyproject.toml` 明示 `requires-python >=3.11`，但只约束可选 second-brain 包；pAI 脚本使用 Python 3 源码而没有锁定最低 Python 版本 | 将来建议选择 Python 3.12 作为**候选开发基线**，由环境验证后正式冻结 | `UNKNOWN` | `python --version`、关键库安装测试；`[需要进一步确认]` |
| Python >=3.9 | K-Dense `skills/sympy/SKILL.md` 对 SymPy 1.14.0 的适配说明 | **来源声明**，不是本项目的安装证据 | `UNKNOWN` | 根据实际 lock 求解，不把第三方文档测试结果当作项目测试 |
| PyYAML | pAI `scripts/release_check.py` 与 `forward_test_demo.py` 调用 `yaml.safe_load`，模块缺失则报错 | 如果将来调用原版检查脚本则需要；自有解析亦可根据依赖策略选用 | `UNKNOWN` | 固定版本、核查安全公告、输入用 `safe_load`；当前不运行 |
| SymPy | K-Dense Skill 声明测试 `sympy==1.14.0`，`mpmath>=1.1,<1.4`，并说明某套 Python/NumPy/SciPy 组合 | 理论分支符号计算候选，不应作为通用 Orchestrator 的安装硬依赖 | `UNKNOWN` | `[需要进一步确认]` 选版本并验证解析正确性/超时预算 |
| NumPy、SciPy | K-Dense Skill 的示例组合注明 NumPy 2.5.3 / SciPy 1.18.1，属于**上游声称的试验快照**，非本仓兼容性保证 | 数值验证/连续策略优化 | `UNKNOWN` | Python ABI、BLAS、求解器容差、可重复性测试；`[需要进一步确认]` |
| Pandas、Matplotlib | pAI `prompts/07b-numerical-simulation.md` 作为首选分析/制图库提及 | 生成数据表与图形；按研究分支可选 | `UNKNOWN` | 版本、许可、图形后端、无 GUI 渲染 |
| Lean 4、mathlib | 后期形式化证明工具设想，不是核心三套上游的安装基础 | 高严格性证明的可选分支 | `UNKNOWN` | 只在明确启用时验证版本/API，不预装 |
| TeX: XeLaTeX、BibTeX | solving-model `phase-5-documentation.md` 明确调用；pAI `CODEX.md` 要求 `pdflatex` | 投稿 LaTeX 生成与编译可选 | `UNKNOWN` | `xelatex --version`、`pdflatex --version`、字体/宏包、`--no-shell-escape`（视引擎支持）；`[需要进一步确认]` |
| Node.js / npm / npx | solving-model `references/phase-1-setup.md`、`oracle-prompts.md` 调用 `npx -y @steipete/oracle` | **非默认依赖**。禁止隐式下载安装作为数学证明的强制步骤 | `UNKNOWN` | 审核包、锁版本、明确授权与隔离才启用；默认 `DISABLED` |
| Git / GitHub CLI | pAI `release_check.py` 在原仓目录调用 `git status` / `git remote` | 用于未来 CI/版本追踪；GitHub 连接器已可进行文档 API 写入 | 目标机 `UNKNOWN` | `git --version`、授权范围、无越权写入 |
| Codex Skill 目录 | Theorist `codex/README.md` 举例复制 `.agents`、`.codex`；pAI 有 `SKILL.md` 与 plugin 包装 | 未来系统宿主之一，须实测 Skill 扫描行为 | `UNKNOWN` | 用户确认 Codex 部署形态、版本、权限、是否重启后可识别 |
| Shell / subprocess | pAI `release_check.py` 使用 `subprocess.run(["git",...])`；Theorist co-math 脚本会写多个新文件 | 开发环境功能；不可授予不受限 shell 给未知来源 PDF/LLM 内容 | `UNKNOWN` | 最小权限、命令白名单/人工批准、隔离临时目录 |
| 网络 / DOI API | 文献模块可能需要 Crossref、Semantic Scholar、出版社；部分外部服务限制访问 | 检索为**可选且有权限限制**的子系统 | `UNKNOWN` | 访问条款、限流、失败降级、出口允许名单、引用核验 |
| GitHub Actions | `MODIFICATION_PLAN.md` Phase 1 才拟引入 CI | 将来执行本仓可审查的静态/单元测试 | **尚无 CI 文件** | Phase 1 获准后建立，运行权限需确认 |
| Windows UTF-8 / Linux / macOS | pAI README 和 `CODEX.md` 提供 Windows UTF-8 注意事项；其他系统未逐项测试 | 跨平台兼容性建议 | `UNKNOWN` | 在实际 OS 上验证文件编码、路径分隔符、subprocess、LaTeX；`[需要进一步确认]` |

**重要区别**：来源项目宣称的“tested with version X”属于 `UPSTREAM_CLAIM`；目标机器当前版本属于 `NOT_OBSERVED`；项目未来选定的 lock 版本属于 `PROPOSED`。三者不得混写为 `INSTALLED_AND_TESTED`。

## 3. 各核心 Skill 的运行轮廓与隐藏依赖

### pAI-Econ-codex

- 研究设计入口：`SKILL.md`、`prompts/*`、`model_library/*` —— 以文本/引导为主，依赖实际宿主的工具能力。
- 自检脚本：`scripts/release_check.py` 与 `forward_test_demo.py`：Python、PyYAML；前者还执行 `git`、检查自身发布目录；不宜原样运行在新仓库。
- 数值阶段：`prompts/07b-numerical-simulation.md` 仅在用户批准后执行，其建议工具为 SymPy、NumPy、SciPy、Pandas、Matplotlib；这些不是项目现阶段已安装的证明。
- 宿主：Codex 插件/Skill 行为与 Agent 子任务须在目标环境单独验收 `[需要进一步确认]`。

### Theorist Toolbox

- Codex 数学证明工作流：以 `SKILL.md`、agent profiles 及独立审查提示为基础；纯文本阅读不需要 Python 依赖。
- `co-math-init/scripts/init_co_math_project.py`：执行会**创建多个目录、`paper.tex`、`AGENTS.md` 等文件**；当前 Phase 0 严禁运行。
- 可选 `second-brain` 包：`requires-python = ">=3.11"`，基础 `marko>=2.0`、`rank-bm25>=0.2.2`；`web` 依赖 `requests>=2.31`、`beautifulsoup4>=4.12`；`providers` 依赖 `anthropic>=0.40`、`openai>=1.40`、`claude-agent-sdk>=0.1`；`mcp` 为 `mcp>=1.2`；`dense` 为 `sentence-transformers>=3.0`；`ocr` 为 `marker-pdf>=1.0`；`dev` 为 `pytest>=8.0`。**全部来自其可选包清单，不得误写为数学证明的强制依赖。**
- 需要 PDF/LaTeX/网络或外部模型时，单独建立最小授权；默认不外传未公开论文。

### solving-model

- `SKILL.md` 设计为 Claude Code sub-agent 工作流，有 `~/.claude/preferences/model-solving-conventions.md`、`verification-protocol.md`、`latex-research.md` 的用户本地配置假设。
- PDF 模型入口依赖独立 `pdf-chunker` Skill；原仓固定 Git Tree 中没有满足本系统需要的完整自包含 PDF 处理契约。
- Oracle 外部审查：`npx -y @steipete/oracle --engine browser --model gpt-5.4-pro`，包含浏览器登录/网络/模型计费潜在依赖。**本项目默认禁用，不因缺 Oracle 就声称验证成功。**
- 整理阶段使用 `xelatex`、`bibtex`；本项目计划用可配置排版适配器，不要求数学建模时必须装 LaTeX。
- 许可证证据不完整，当前 `BLOCK_COPY`，不可安装/打包原 Skill 代码或提示文件。其方法结构可作为独立新实现的参考。

## 4. 推荐部署 Profile（**建议，不是已批准的安装计划**）

| Profile | 需要的能力 | 明确不依赖 | 当前结论 |
|---|---|---|---|
| `core-offline` | Python 可执行、JSON Schema 校验、项目本地读写（未来 Phase 1） | Oracle、LLM API、TeX、浏览器、付费数据库 | `PROPOSED / NOT_TESTED` |
| `theory-symbolic` | `core-offline` + SymPy、符号运算预算、可行域检查 | Gambit、Lean、Oracle 不是强制 | `PROPOSED / NOT_TESTED` |
| `theory-numerical` | `theory-symbolic` + NumPy、SciPy，必要时 Pandas/Matplotlib | 强制访问外网 | `PROPOSED / NOT_TESTED` |
| `manuscript` | `core-offline` + LaTeX 引擎或受控文稿导出模块 | 外部 PDF 下载/Oracle 不是强制 | `PROPOSED / NOT_TESTED` |
| `literature-online` | `core-offline` + 已批准的学术检索网络/密钥 | 不应默认上载私人 PDF 全文 | `PROPOSED / NOT_TESTED` |
| `empirical` | Python/R/Stata 按数据来源和模型另行授权 | 不把实证环境强加于理论博弈 | `DEFER` |
| `formal-proof` | Lean 4 + mathlib + 形式化适配流程 | 不得替换经济假设合法性审查 | `DEFER` |

## 5. 初次真实部署时的必要验证（Phase 1 获授权后再执行）

1. 确定目标宿主的 **OS、Codex 形态与版本、网络/安全沙盒、CPU/RAM、是否允许新建文件、私有论文驻留位置、预算与账号许可** `[需要进一步确认]`。
2. 使用独立环境收集 `python --version`、`git --version`、`node --version`、`npm --version`、`xelatex --version`（不存在要记 `MISSING`，不能解释为“安装失败”）。
3. 通过包管理器生成固定版本的锁文件及依赖许可证/SBOM；安装前核对 Python 与平台 wheel 兼容性。
4. 在无网络的测试夹具上验证 Symbolic 基准：准确有理数、FOC 回代、二阶条件、KKT 边界、限制性比较静态、已知反例。
5. 单独测试 API 和数据权限；网络不可用时应返回 `UNAVAILABLE`，不得伪造引用、默认调用外部模型或持续重试。
6. 在目标 Codex 会话中核验 Skill 发现、手动触发、可选 agent 角色；不要将当前 ChatGPT 的工具能力作为证据。
7. PDF/LaTeX 输入经文本提取和安全审查后才进入模型 DSL；绝不能将 PDF 中的可执行指令交给 shell。
8. 为数学运算设置时间、内存、表达式长度/深度预算；未知或超限返回 `UNRESOLVED` / `RESOURCE_LIMIT`，不悄悄降精度宣布证明。
9. 把每一次部署报告附操作系统、包版本、依赖树、日期及最小测试结果；留存失败记录。

## 6. 环境决策与状态

- 已完成的是**需求证据审查**，不是目标部署机的 `python`、`Codex`、`node`、`TeX` 安装验证。
- 阻断 Phase 1 的环境未知：目标宿主/网络与数据出口、具体 Python 与数学包兼容版本、未来用户选择的许可证和依赖许可策略；`[需要进一步确认]`。
- Phase 0B 的审核文档可以入库，且允许保留 `UNKNOWN`；**这不能视为环境已满足 Phase 1 验收**。
- 当遇到第三方工具不可用，应选择“替代方案/延期”，不得自动安装、越权调用或假装通过。
