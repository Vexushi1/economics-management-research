# DEPENDENCY_RISKS.md — 第三方依赖风险、输入安全与质量门审计

> Phase 0B 文档 / 2026-10-12。对应 `MODIFICATION_PLAN.md` Phase 0、后续 Phase 1–9。  
> **审计方法**：只读检查 GitHub 固定版本的关键文件、依赖声明和命令示例；未运行第三方代码、未安装包、未启用网络 API、未对目标 Codex 环境进行渗透或端到端测试。  
> 优先级：`CRITICAL` 直接阻断不安全执行/再发布；`HIGH` 必须有控制和验证后使用；`MEDIUM` 可延期但须记录。风险评估为工程判断，不等同已发生漏洞。

## 1. 信任边界与安全基准

`用户上传 PDF / 学术网页 / 上游 SKILL 文本 / LLM 输出` 全部视为**不可信数据**；`经过许可和安全审查的结构化 ModelSpec、求解脚本、源代码` 才可进入后续工具。不得把论文内的文字命令、参考文献链接或方程字符串直接提升为系统指令或 shell 命令。

推荐边界：

1. `UNTRUSTED_DOCUMENT` → PDF/TeX/HTML 静态提取、保留页码与来源（禁止执行其中的命令）。
2. `UNTRUSTED_MODEL_TEXT` → 明确变量与参数清单、数学式 AST/DSL 白名单解析、资源预算。
3. `VALIDATED_MODEL_SPEC` → 独立求解器接口（有明确模型版本、参数域、单位、状态）。
4. `SYMBOLIC_RESULT`/`NUMERICAL_RESULT` → 回代、边界/极值和反例审查；不能等同严格证明。
5. `VERIFIED_CLAIM` → 记录验证方式、证据、限制与审查者，供论文写作引用。
6. 外部联网、写文件、安装、运行 TeX/脚本等有副作用的操作须在授权范围内；无授权即 `DENIED`。

**当前 Phase 0B 只有纯 Markdown 文件，不应产生 `src/`、`SKILL.md`、`pyproject.toml` 或任何可执行文件。**

## 2. 风险登记册

| ID | 风险及来源 | 严重度 | 现状/证据 | 缓解与验证 | 阶段门 |
|---|---|---|---|---|---|
| R01 | **solving-model 源码许可依据不完整** | CRITICAL | README 写 MIT，固定 SHA 未见适用完整 LICENSE | `BLOCK_COPY`；获得权利人书面/可追溯授权或独立重新实现；留版本和文件级许可证据 | 复用前 |
| R02 | 上游来源文件含第三方版权、混合授权 | HIGH | pAI 为适配版且保留 NOTICE；经济学写作库 CC BY-NC 分层 | 逐文件许可/SBOM；保留 MIT/Apache NOTICE；不得删原作者声明 | 复制前 |
| R03 | Oracle `npx -y` 隐式下载安装并执行代码 | CRITICAL | solving-model 多阶段给出 `npx -y @steipete/oracle` | 默认禁用；若将来批准：人工确认、固定软件版本、供应链审查、受限沙盒，禁止自动重试 | 外部执行前 |
| R04 | Oracle 浏览器手动登录、上传未公开理论模型 | CRITICAL | 原版 `--engine browser`、`--browser-manual-login` | 不作为数学证明强制前置；确认隐私政策、合同、授权、数据分类，禁止未授权外传 | 任何外部 API |
| R05 | 私人 Claude 路径或缺失偏好文件 | HIGH | solving-model 引用 `~/.claude/preferences/...`，仓库 tree 没有这些文件 | 自有配置 schema/defaults，适配器显式声明缺失；不能静默猜测 | 理论设计集成前 |
| R06 | `pdf-chunker` 等隐式 Skill 不存在 | HIGH | solving-model Phase 1 PDF 处理明确调用另一个 Skill | 改为可选 PDF adapter；无能力应报告 `UNAVAILABLE`；保留页码/公式来源 | 阅读/复现模块 |
| R07 | pAI 自检脚本与上游固定目录耦合 | MEDIUM | `release_check.py` 预设上游 plugin、Git 结构，并调用 `git status` | 不直接将其当作新仓 CI；独立编写新仓校验，先检验工具副作用 | Phase 1/CI |
| R08 | Theorist `co-math-init` 执行产生大量新文件 | HIGH | Python 脚本会生成 `paper.tex`、`AGENTS.md`、`workstreams`、registry | 当前不执行；未来需独立临时目录、路径白名单、事前 diff 与人工批准 | co-math 启用前 |
| R09 | 公式字符串代码注入 | **CRITICAL** | 尚未开发模型 DSL；用户/PDF/LLM 输入无法信任 | 详见第 3 节；禁用字符串 `eval/exec`；仅允许审核过的数学 AST；限制资源 | 任何符号解析前 |
| R10 | SymPy `sympify`/`parse_expr` 直接处理不可信字符串 | **CRITICAL** | 某些便捷接口含动态表达式求值路径，不能等同安全解析 | 不将其用于未经验证的原始表达式；先用自己的小语法/AST，映射白名单 `Symbol`/`Integer`/`Add`/`Mul` 等 | 数学引擎设计前 |
| R11 | `lambdify`/编译/代码生成绕过隔离 | HIGH | 数学式可能生成并运行 Python/NumPy 表达式 | 仅对来自已验证 AST 的受限表达式在沙盒使用，默认禁用用户可控模块/函数映射 | 数值实验前 |
| R12 | 数学资源耗尽（超大指数、嵌套、符号爆炸） | HIGH | SymPy 求解和化简可能超时、耗尽内存 | 限长度、深度、符号数、指数、求解超时与内存；超限 `RESOURCE_LIMIT`，不得报告证明成功 | Phase 4 |
| R13 | 约束、边界、分段模型丢失而误判最优 | HIGH | 理论模型涉及 KKT、IR/IC、全局与局部极值 | 参数域显式记录；FOC 不能代替均衡；测试边界、二阶/全局候选与反例 | Phase 4–6 |
| R14 | 多 Agent 自洽但同错、错误命题写入正文 | HIGH | Theorist 提供对抗审查，但非自动形式验证 | 证明义务、独立推导、符号回代、反例；`GAP` 不得升级为 `PROVED`；必要时 Lean 形式化 | 论文写作前 |
| R15 | PDF/网页 prompt injection | HIGH | 研究文献、仓库 README 中可含“忽略指令”等文本 | 数据与指令分层，不允许文献决定执行计划/外传、忽略许可；可记录恶意段落以审计 | 所有导入 |
| R16 | LaTeX/工具链执行不可信宏和文件 | HIGH | solving-model 使用 `xelatex`/`bibtex`，pAI 使用 `pdflatex` | 不编译未经审查的 TeX，禁 shell escape，限制输入路径与输出目录，沙盒；对宏包及 BibTeX 数据做检查 | 稿件编译前 |
| R17 | Python/Node 依赖供应链污染或版本漂移 | HIGH | 未锁 Python/Node 包；某些示例通过 npx 动态安装 | lock + 依赖哈希 + SBOM + 安全公告核查；离线测试，升级需回归 | Phase 1/升级 |
| R18 | 模型/论文/秘密经外部服务泄露 | CRITICAL | 文献检索、Oracle、LLM providers 可能联网 | 敏感度标记、出站域名白名单、最小化内容、明确用户批准、密钥环境注入/脱敏日志 | 外部服务前 |
| R19 | 学术 API 速率/版权/付费墙限制 | MEDIUM | Crossref/Semantic Scholar/CNKI 等权限各异 | 合规访问、限流/缓存、失败降级、不得模拟授权或绕反爬 | 文献系统 |
| R20 | 数值仿真被误称“证明”，复现被误称“验证” | HIGH | 上游 smoke test 仅流程测试，局部样本不能穷尽参数域 | 分离 `CONSISTENT`/`REPRODUCED`/`PROVED` 状态，附代码环境与误差预算 | Phase 4–9 |
| R21 | 上游 CLI/代理只支持特定宿主 | HIGH | Theorist Codex 版/Claude 版位置不同，pAI 有插件包装 | 按目标宿主逐一实测；不存在则 `UNAVAILABLE`，不猜命令参数 | Phase 1 |
| R22 | 科研工件失效传播遗漏 | HIGH | 后续计划依赖假设→均衡→命题→论文链条 | 最小 DAG 失效提前在 Phase 1 实现，修改模型自动标记下游 `STALE`；回归测试 | Phase 1–9 |
| R23 | GitHub 多文件写入造成中间态 | MEDIUM | Contents API 每次建文件单独 Commit | 每次写入后读回 SHA、目录枚举；提交范围限四文件；必要时按授权修复，不覆盖其它文件 | Phase 0B |
| R24 | 未知目标运行环境被写成已通过 | HIGH | 当前 GitHub 可访问 != 用户 Codex 可执行 | `ENVIRONMENT_MATRIX.md` 记录 `UNKNOWN`，待真实宿主/版本/网络实测后才能变为 `VERIFIED` | Phase 0→1 |

所有风险都保留证据与控制建议；某项已发现并不意味着漏洞已利用，未发现也不代表不存在。

## 3. 模型公式解析：强制安全设计要求

### 3.1 禁止的捷径

**不得**把 PDF、网页、LLM 输出、用户原始字符串作为 Python 表达式交给下列接口直接求值：

`eval(...)`、`exec(...)`、`compile(...)`、动态 `__import__`、`getattr`/反射链、`subprocess`、`os.system`、`pickle.loads`。

对不可信原始文本，也**不得直接调用** `sympy.sympify(raw_text)` 或 `sympy.parsing.sympy_parser.parse_expr(raw_text)` 并假定安全。前者可能解析出危险 Python 结构，后者涉及表达式求值；“数学库函数”并不自动是可信输入沙盒。

### 3.2 建议的最小安全 DSL

建议由独立验证过的 tokenizer/parser 接收严格受限语法，或使用 `ast.parse(text, mode="eval")` **只生成解析树，然后逐节点白名单校验；绝不 `eval/compile` 该树**。允许的例子：

- 已注册变量名，例如 `p`、`e`、`lambda`；名称集合事先存在 `model-spec`，未知名称拒绝。
- 有界整数/十进制数（按精度政策转换为 `Integer`、`Rational`）；禁止 NaN/Inf、复杂可执行类型。
- 基础运算 `+`、`-`、`*`、`/` 和受限幂运算；若使用函数，则通过显式字典映射到安全数学函数，拒绝任意属性/方法访问。
- 禁止 `Call`（除注册的纯数学函数）、`Attribute`、`Subscript`、`Lambda`、`ListComp`、`DictComp`、`Await`、`NamedExpr`、`IfExp`、`JoinedStr`、`GeneratorExp` 等非数学节点。
- 排序/比较、积分、分段、概率分布等高级模型**不靠开放 Python 执行**扩展；采用独立 JSON schema/受审计 DSL 版本和纯函数构造器。
- 任何转换到 SymPy `Symbol`、`Add`、`Mul`、`Pow`、`Piecewise` 的行为都必须在验证通过以后进行。

### 3.3 必须限制资源与输出

- 输入字符/字节数、解析节点数、嵌套深度、变量数量、指数绝对值、展开项数、输出表达式大小：各自设可配置上限，**具体数值尚未性能测试** `[需要进一步确认]`。
- 简化/求解运行在独立、权限受限的进程，设置 wall-clock 与 CPU/内存预算；Python 线程级超时不等于可靠的强制终止。
- 即使 DSL 无代码执行能力，也要防**算法复杂度 DoS**，如构造巨大指数或触发昂贵 Groebner/求根过程。
- 生成 LaTeX/绘图标签需再次转义、限定路径，不能将数学字符串插入 shell 命令。
- 若 AST 验证失败返回 `INVALID_EXPRESSION`；若预算耗尽返回 `RESOURCE_LIMIT`；若无法证明返回 `UNRESOLVED`。三者不能合并成 `PROVED` 或静默通过。

### 3.4 未来必须做的安全测试（尚未执行）

| 测试类别 | 输入示例/检测意图 | 必须结果 |
|---|---|---|
| 基础表达式 | `p + 2*e`，变量 `p,e` 已登记 | 解析成功、精确回代 |
| 未授权名字 | `secret + p`，`secret` 未登记 | 拒绝 |
| 恶意调用 | `__import__("os").system("echo bad")` | 拒绝，绝无副作用 |
| 属性访问 | `p.__class__` | 拒绝 |
| 表达式滥用 | 巨大幂 `p**999999999` | 拒绝或预算控制退出 |
| 超深嵌套 | 极长括号嵌套、巨量变量 | 拒绝或 `RESOURCE_LIMIT` |
| Prompt injection | PDF 正文中“执行 shell / 删除文件” | 仅做引用文本，不能触发命令 |
| 代码生成 | 输入公式尝试调用 `lambdify` 任意模块 | 拒绝未批准的函数/模块 |
| TeX shell escape | 带有 `\write18` 的不可信片段 | 不执行，记录输入拒绝/隔离 |
| 路径穿越 | `../../private` 作为输出名 | 拒绝 |

这些是 **Phase 1/3/4 的待实现测试规格**，不是已运行测试结果。

## 4. 质量门与执行权限规则

### Phase 0A / 0B（当前）

- `0A READ_ONLY`：核对固定 SHA、README/许可证、文件树、脚本入口与环境要求；可将无法观察的事实标 `UNKNOWN`。
- `0B DOCUMENTATION`：只创建四份 Markdown 审计文件。不得复制 Skills、建立包、安装依赖或运行任何上游脚本。
- `0B 完成判定`：四文件存在、读回匹配、阻断项没有被改写成通过、提交文件范围符合授权。**仅“文档落地完成”，不等于第三方依赖通过准入审查**。

### Phase 1 及后续（尚未授权）

- **许可门**：待复制的具体文件必须具备可验证的再分发权；`solving-model` 当前 `BLOCK_COPY`。如实施只复用抽象方法，可以用独立实现作为替代，仍需报告路径。
- **环境门**：目标 OS/Codex/Python、权限与私有数据出口均为 `[需要进一步确认]`；不得借“当前 ChatGPT 有工具”推断目标机器已准备。
- **安全门**：在接收任何外部/LLM 生成方程前，须先实现受限解析器与资源预算；禁止直接 `sympify` 未审核文本。
- **理论门**：符号回代、二阶/全局条件、约束、反例与命题证明分别审计；`GAP`、`UNRESOLVED`、`FALSE` 不能当 `PROVED`。
- **审稿门**：引用真实性、论断支持、复现环境与目标期刊规范分别检查，避免“找到 DOI 即证明论断”。

## 5. 风险跟踪与下一步

| 决策 | 当前结论 | 解除条件 |
|---|---|---|
| 直接复制 pAI-Econ-codex / Theorist Toolbox | 仅许可证文本已查，尚未开展复制或逐文件安全审计 | Phase 1 获明确授权 + 核查拟复制文件/依赖 |
| 直接复制 solving-model | **BLOCKED** `[需要进一步确认]` | 权利人确认授权或独立重写 |
| 运行 Oracle / npx / 浏览器登录 | **DISABLED** `[需要进一步确认]` | 外部脚本与隐私评估、用户明确授权 |
| 采用 `SymPy` 处理外部公式 | **设计可行、部署未验收** | 受限 AST/DSL + 反例/安全测试 + 资源隔离 |
| 进入 Phase 1 | **NOT AUTHORIZED**；关键环境/许可事项未关闭 | 新的工程授权、明确是否以独立实现绕开许可阻断、选定目标宿主与基础版本 |

**工程判断**：已识别可复用的研究思路和主要隐藏依赖；仍存在未经验证的运行环境与许可问题。本风险文件不宣称安全审计完全覆盖或不存在未知漏洞。后续发现新风险应新增审计记录，而不是删除旧记录。
