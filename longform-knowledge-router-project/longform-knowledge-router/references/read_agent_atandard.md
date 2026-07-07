
# 长文多模态知识路由 Skill / Agent 通用构建标准

版本：v0.1
目标对象：书籍、论文集、长篇报告、教材、档案、复杂 PDF / EPUB / DOCX 文档
核心目标：将长文编译为 Markdown、图集、原文映射和多层知识路由网络，使后续 AI 能基于知识路径定位、阅读、验证和引用原文，而不是依赖传统文本相似度检索。

---

## 1. 总目标

本标准定义一种通用 Skill / Agent 架构，用于完成以下任务：

1. 将长文转换为结构化 Markdown。
2. 提取文档中的图片、图表、表格、公式、页面截图等视觉资产，生成图集。
3. 为每个文本段落、图片、图表、表格、标题、脚注、页码建立原位置映射。
4. 从全文中抽取原子知识单元。
5. 构建多层知识路由网络。
6. 使后续 AI 可以通过“知识路径”定位任意相关原文。
7. 支持局部精读、全局综述、跨章节追踪、论证链追踪、概念演化追踪、图文互证。
8. 避免把系统退化为传统 chunk embedding RAG。

一句话目标：

> 将一本书从“可搜索文本”编译成“可执行的知识地图”。

---

## 2. 非目标

本系统不应被设计成以下形态：

1. 不是单纯的 PDF 转 Markdown 工具。
2. 不是单纯的 OCR / 版面解析工具。
3. 不是单纯的向量数据库检索系统。
4. 不是只返回 top-k chunks 的 RAG 系统。
5. 不是仅生成摘要的读书笔记工具。
6. 不是无法回指原文的知识图谱。
7. 不是无法验证来源的自动问答系统。
8. 不是只靠文本匹配定位信息的搜索器。

---

## 3. 核心设计哲学

### 3.1 文本是证据，不是知识本身

系统不得直接把 chunk 当作知识节点。
chunk、段落、页码、bbox、Markdown anchor 都应被视为证据容器。

真正的知识节点应是：

* 定义
* 概念
* 命题
* 事实
* 论点
* 论据
* 反例
* 例子
* 过程步骤
* 人物
* 事件
* 方法
* 术语
* 图像说明
* 图表结论
* 章节主题
* 论证结构

### 3.2 摘要是路标，不是证据

任何摘要、主题节点、社区节点、章节概括都只能用于导航。
最终回答、引用、验证必须能够回到原文证据。

每个抽象节点必须可逆地追溯到：

* supporting atoms
* source spans
* source pages
* markdown anchors
* figure IDs
* table IDs
* bbox 坐标

### 3.3 检索结果应是路径，而不是无序片段

系统的核心输出不应是：

```text
[top chunk 1, top chunk 2, top chunk 3]
```

而应是：

```text
问题意图
→ 入口节点
→ 主题节点
→ 概念节点
→ 命题节点
→ 证据节点
→ 原文位置
```

也就是说，检索的基本结果是 route path，而不是 passage list。

### 3.4 树负责范围，图负责关系，路径负责行动

知识路由网络必须同时包含：

1. 结构树：书、部、章、节、段、图、表。
2. 抽象树：主题、子主题、知识簇、摘要层。
3. 语义图：概念、实体、命题、关系、论证、引用。
4. 路径索引：从问题意图到证据节点的可执行路线。

### 3.5 最小充分证据优先于最大召回

系统应优先返回结构上连贯、证据充足、噪声较少的路径集合。
不得以“召回越多越好”为核心指标。

推荐目标：

```text
minimum sufficient evidence set
最小充分证据集
```

### 3.6 原书只吸收一次，查询时多步激活

“只读一遍”的工程含义是：

1. 原始书籍只做一次结构化解析和知识吸收。
2. 后续查询不重新扫描整本书。
3. 后续 AI 在已构建的知识空间中多步导航、激活、验证和引用。

---

## 4. 系统总体架构

标准系统应包含四个核心层：

```text
Long-form Knowledge Routing Skill / Agent
│
├── 1. Provenance Layer
│   ├── page
│   ├── bbox
│   ├── text span
│   ├── markdown anchor
│   ├── figure asset
│   └── table / formula / footnote location
│
├── 2. Atomic Knowledge Layer
│   ├── concepts
│   ├── definitions
│   ├── claims
│   ├── facts
│   ├── arguments
│   ├── examples
│   ├── figures
│   └── evidence atoms
│
├── 3. Topology Layer
│   ├── structural tree
│   ├── semantic graph
│   ├── abstraction tree
│   ├── argument graph
│   ├── figure-text graph
│   └── route path index
│
└── 4. Routing Policy Layer
    ├── entry selection
    ├── path expansion
    ├── neighbor traversal
    ├── evidence inspection
    ├── contradiction check
    ├── source verification
    └── answer assembly
```

---

## 5. Skill / Agent 标准目录结构

推荐目录结构：

```text
book-route-skill/
│
├── SKILL.md
├── README.md
├── schemas/
│   ├── document.schema.json
│   ├── source_span.schema.json
│   ├── figure.schema.json
│   ├── knowledge_atom.schema.json
│   ├── route_node.schema.json
│   ├── route_edge.schema.json
│   ├── route_path.schema.json
│   └── build_report.schema.json
│
├── scripts/
│   ├── ingest.py
│   ├── parse_document.py
│   ├── extract_assets.py
│   ├── describe_figures.py
│   ├── build_source_map.py
│   ├── extract_atoms.py
│   ├── build_structural_tree.py
│   ├── build_semantic_graph.py
│   ├── build_abstraction_tree.py
│   ├── build_route_index.py
│   ├── query_route.py
│   ├── verify_evidence.py
│   └── repair_index.py
│
├── prompts/
│   ├── atom_extraction.md
│   ├── figure_description.md
│   ├── route_node_generation.md
│   ├── route_edge_generation.md
│   ├── route_query_planning.md
│   └── evidence_verification.md
│
├── output/
│   ├── book.md
│   ├── assets/
│   ├── figures.jsonl
│   ├── tables.jsonl
│   ├── source_spans.jsonl
│   ├── atoms.jsonl
│   ├── route_nodes.jsonl
│   ├── route_edges.jsonl
│   ├── route_paths.jsonl
│   ├── route_graph.json
│   ├── route_index.sqlite
│   ├── build_report.md
│   └── errors.jsonl
│
└── tests/
    ├── fixture_book/
    ├── expected_schema/
    ├── route_queries.jsonl
    └── evaluation.md
```

---

## 6. 必需输出物标准

每次构建必须至少产生以下文件。

### 6.1 `book.md`

完整 Markdown 正文。

要求：

1. 保留章节层级。
2. 保留页码锚点。
3. 保留图像、表格、公式引用。
4. 每个重要段落应有稳定 anchor。
5. 不得丢失脚注、边注、标题、图题、表题。
6. 不得把图像说明和正文关系打散。

推荐格式：

```markdown
<a id="p0123-b004"></a>

## 3.2 记忆与身份

原文段落……

![Figure 3.2](assets/fig_0032.png)

<figure-anchor id="fig_0032" source_page="123" source_bbox="72,140,510,612" />
```

---

### 6.2 `assets/`

存放所有视觉资产。

包括：

* 原始图片
* 图表截图
* 表格截图
* 公式截图
* 页面区域截图
* 必要时的整页截图

命名规范：

```text
fig_0001.png
fig_0002.png
table_0001.png
formula_0001.png
page_0123_region_0004.png
```

---

### 6.3 `figures.jsonl`

每行记录一个视觉资产。

必需字段：

```json
{
  "figure_id": "fig_0032",
  "asset_path": "assets/fig_0032.png",
  "type": "chart | illustration | diagram | photo | table | formula | page_region",
  "title": "图 3.2 记忆连续性模型",
  "caption": "原图题或表题",
  "detailed_description": "对图像内容的详细描述",
  "visual_elements": ["箭头", "时间轴", "人物节点"],
  "semantic_role": "解释概念 | 支持论点 | 给出例子 | 展示流程 | 呈现数据",
  "related_atoms": ["atom_10231", "atom_10232"],
  "related_route_nodes": ["concept.memory-continuity"],
  "source_page": 123,
  "source_bbox": [72, 140, 510, 612],
  "markdown_anchor": "book.md#fig_0032"
}
```

要求：

1. 图像描述必须是可检索的自然语言。
2. 图像必须和正文知识节点建立关系。
3. 图像必须能反向定位到原页面位置。
4. 正文段落也必须能反向找到相关图像。

---

### 6.4 `source_spans.jsonl`

记录原文位置单元。

必需字段：

```json
{
  "source_span_id": "span_p0123_b004",
  "document_id": "book_001",
  "page": 123,
  "block_id": "b004",
  "block_type": "paragraph | heading | figure | table | footnote | formula | caption",
  "text": "原文文本或提取文本",
  "markdown_anchor": "book.md#p0123-b004",
  "bbox": [72, 140, 510, 612],
  "char_start": 184203,
  "char_end": 185011,
  "related_atoms": ["atom_10231"],
  "related_route_nodes": ["claim.identity-memory-001"]
}
```

要求：

1. 每个知识节点必须能追溯到至少一个 source span。
2. 每个 source span 应记录其承载的知识 atoms。
3. 若 bbox 不可用，必须明确标记 `bbox: null`，不得伪造坐标。
4. 若 OCR 不确定，必须记录置信度。

---

### 6.5 `atoms.jsonl`

记录原子知识单元。

知识 atom 是系统的基础知识粒度。

必需字段：

```json
{
  "atom_id": "atom_10231",
  "type": "definition | claim | fact | example | argument_step | counterexample | method | event | concept_note | figure_interpretation",
  "content": "作者将身份理解为记忆连续性的结果。",
  "normalized_content": "身份由记忆连续性构成。",
  "source_spans": ["span_p0123_b004"],
  "supporting_figures": ["fig_0032"],
  "entities": ["identity", "memory"],
  "concepts": ["memory_continuity", "personal_identity"],
  "certainty": "explicit | inferred | ambiguous",
  "local_context": "本段位于第三章第二节，讨论个人身份的心理连续性理论。",
  "route_nodes": ["claim.identity-memory-001"]
}
```

要求：

1. atom 必须自包含。
2. atom 必须可追溯到原文。
3. atom 不应混入多个无关知识点。
4. atom 类型必须清晰。
5. atom 的抽取应尽量稳定，允许后续修复。

---

### 6.6 `route_nodes.jsonl`

记录路由节点。

路由节点是后续 AI 导航的主索引单位。

必需字段：

```json
{
  "route_node_id": "concept.personal-identity.memory-continuity",
  "type": "book | part | chapter | section | topic | concept | entity | claim | argument | figure | evidence | question_route",
  "title": "记忆连续性与个人身份",
  "summary": "本节点汇集书中关于记忆连续性如何构成个人身份的讨论。",
  "level": 3,
  "parent_nodes": ["chapter.03"],
  "child_nodes": ["claim.identity-memory-001", "example.locke-case"],
  "related_atoms": ["atom_10231", "atom_10232"],
  "source_spans": ["span_p0123_b004", "span_p0124_b001"],
  "figures": ["fig_0032"],
  "can_answer": [
    "作者如何定义个人身份？",
    "记忆连续性在论证中起什么作用？"
  ],
  "cannot_answer": [
    "该理论在现代神经科学中的最新证据。"
  ],
  "confidence": 0.87,
  "status": "verified | draft | needs_review"
}
```

要求：

1. 路由节点不得无证据。
2. 抽象节点必须能下钻到 atom。
3. 节点必须声明适合回答什么问题。
4. 节点必须声明不能回答什么问题。
5. 节点应具有稳定 ID。

---

### 6.7 `route_edges.jsonl`

记录路由边。

必需字段：

```json
{
  "edge_id": "edge_55021",
  "source": "concept.memory-continuity",
  "target": "claim.identity-memory-001",
  "type": "defines | supports | refutes | contrasts | exemplifies | part_of | explains | depends_on | cites | appears_in | related_to | hypothesis",
  "edge_class": "hard | semantic | hypothesis",
  "description": "该命题用来支持记忆连续性概念。",
  "evidence_spans": ["span_p0123_b004"],
  "confidence": 0.82,
  "created_by": "layout | parser | model | human | repair",
  "status": "verified | draft | rejected"
}
```

边分为三类：

#### hard edges

来自版面、目录、显式引用、图文位置关系。
例如：

* part_of
* located_at
* appears_in
* caption_of
* cites
* same_as

#### semantic edges

来自语义抽取，需要证据支持。
例如：

* defines
* explains
* supports
* refutes
* contrasts
* exemplifies
* depends_on

#### hypothesis edges

用于探索，不得直接作为最终证据。
例如：

* related_to
* thematic_echo
* analogy_to
* may_imply

要求：

1. hard edge 优先可信。
2. semantic edge 必须带证据。
3. hypothesis edge 必须清楚标记，不得混入正式引用。
4. 边必须可被删除、修正、降级。

---

### 6.8 `route_paths.jsonl`

记录常用知识路径。

必需字段：

```json
{
  "path_id": "path.personal-identity.memory-argument",
  "intent": "解释作者如何论证记忆与个人身份的关系",
  "entry_nodes": ["chapter.03", "concept.personal-identity"],
  "steps": [
    {
      "node": "chapter.03",
      "action": "drill_down",
      "reason": "第三章是个人身份讨论的主章节。"
    },
    {
      "node": "concept.memory-continuity",
      "action": "follow_concept",
      "reason": "该概念是本论证的核心。"
    },
    {
      "node": "claim.identity-memory-001",
      "action": "inspect_claim",
      "reason": "该命题直接表述作者主张。"
    },
    {
      "node": "span_p0123_b004",
      "action": "verify_source",
      "reason": "回到原文验证。"
    }
  ],
  "supporting_atoms": ["atom_10231", "atom_10232"],
  "source_spans": ["span_p0123_b004"],
  "figures": ["fig_0032"],
  "path_confidence": 0.84
}
```

要求：

1. 路径必须表达“为什么走到这里”。
2. 路径必须能落到原文。
3. 路径必须支持展开、压缩和验证。
4. 路径应可缓存，但不得替代动态导航。

---

## 7. 路由网络必须支持的查询动作

Agent 不应只暴露 `search(query)`。
标准 Agent 应至少支持以下工具动作。

### 7.1 入口选择

```text
find_entry_points(question) -> route_node[]
```

用途：根据问题意图找到可能进入知识网络的节点。

返回：

* 章节入口
* 主题入口
* 概念入口
* 实体入口
* 图像入口
* 论证入口

---

### 7.2 路径规划

```text
plan_route(question, entry_nodes, mode) -> route_plan
```

模式：

```text
local_reading
global_synthesis
concept_trace
argument_trace
figure_trace
counter_evidence
source_verification
```

---

### 7.3 节点读取

```text
read_node(route_node_id) -> node_summary + evidence_preview
```

要求：

1. 返回节点摘要。
2. 返回可下钻子节点。
3. 返回相关边。
4. 返回证据预览。
5. 明确该节点是否足够回答问题。

---

### 7.4 邻居扩展

```text
read_neighbors(route_node_id, edge_types, max_depth, budget) -> neighbor_nodes
```

要求：

1. 可按边类型过滤。
2. 可按置信度过滤。
3. 可限制预算。
4. 可排除 hypothesis edges。

---

### 7.5 路径展开

```text
expand_path(path_id, strategy, budget) -> route_path
```

策略：

```text
coarse_to_fine
evidence_first
argument_first
concept_first
figure_first
counterexample_first
```

---

### 7.6 证据检查

```text
inspect_evidence(route_node_id) -> source_span[]
```

必须返回：

* 原文文本
* 页码
* bbox
* Markdown anchor
* 相关图片
* 相关 atom
* 证据是否直接支持该节点

---

### 7.7 回到原文

```text
jump_to_source(source_span_id) -> source_context
```

返回：

* 前后文
* 页面位置
* Markdown 位置
* 图片/表格邻接内容
* 所属章节路径

---

### 7.8 反证搜索

```text
find_counter_evidence(claim_node_id) -> route_path[]
```

用于寻找：

* 反例
* 限制条件
* 作者自我修正
* 其他章节中的相反表述
* 脚注或附录中的限定说明

---

### 7.9 路径压缩

```text
summarize_path(path_id) -> path_summary
```

要求：

1. 压缩路径时不得丢失证据。
2. 压缩结果必须保留 source span 引用。
3. 压缩摘要不得声称超出证据的内容。

---

### 7.10 验证回答

```text
verify_answer_against_sources(answer, source_spans) -> verification_report
```

检查：

* 是否有证据支持
* 是否误读原文
* 是否过度概括
* 是否混入外部知识
* 是否引用了 hypothesis edge
* 是否需要更多路径

---

## 8. 构建流程标准

### 8.1 阶段一：文档吸收

输入：

```text
PDF / EPUB / DOCX / HTML / Markdown / Images
```

输出：

```text
raw blocks
layout blocks
page images
text spans
asset candidates
```

要求：

1. 保留页级结构。
2. 保留阅读顺序。
3. 保留标题层级。
4. 保留图表位置。
5. 保留脚注、尾注、边注。
6. 对低置信 OCR 做标记。

---

### 8.2 阶段二：Markdown 与资产生成

输出：

```text
book.md
assets/
figures.jsonl
tables.jsonl
```

要求：

1. Markdown 可读。
2. Markdown 可定位。
3. 图片和表格有稳定 ID。
4. 图像描述足够详细。
5. 图像必须和原文位置双向映射。

---

### 8.3 阶段三：source map 构建

输出：

```text
source_spans.jsonl
```

要求：

1. 每个 Markdown anchor 对应原文位置。
2. 每个 source span 对应 Markdown 位置。
3. 每个图片、表格、公式都可双向跳转。
4. 每个 source span 可关联多个知识 atom。
5. 不确定映射必须显式标记。

---

### 8.4 阶段四：知识 atom 抽取

输入：

```text
source_spans
local context
figure descriptions
section headings
```

输出：

```text
atoms.jsonl
```

抽取规则：

1. 每个 atom 应表达一个最小知识功能。
2. atom 必须自包含。
3. atom 必须有 source span。
4. atom 应保留原文语义，不得过度改写。
5. atom 类型必须明确。
6. 不确定内容标记为 ambiguous。
7. 推断内容标记为 inferred。

---

### 8.5 阶段五：结构树构建

输出：

```text
structural_tree
```

包含：

```text
book
part
chapter
section
subsection
paragraph
figure
table
footnote
appendix
```

要求：

1. 基于文档结构和版面，不依赖语义猜测。
2. 每个结构节点必须有 source span 或 asset。
3. 结构树是最高可信导航骨架。

---

### 8.6 阶段六：语义图构建

输出：

```text
semantic_graph
```

节点：

```text
concept
entity
claim
definition
argument
example
event
method
figure_interpretation
```

边：

```text
defines
supports
refutes
contrasts
explains
depends_on
exemplifies
appears_in
cites
```

要求：

1. 语义边必须有证据。
2. 模型推断边必须有 confidence。
3. 不稳定关系应放入 hypothesis layer。
4. 同义概念应建立 alias / same_as 关系。
5. 概念跨章节出现时应建立 evolution / recurrence 关系。

---

### 8.7 阶段七：抽象树构建

输出：

```text
abstraction_tree
```

包含：

```text
book themes
chapter themes
section themes
concept clusters
argument clusters
evidence clusters
```

要求：

1. 抽象节点只用于导航。
2. 抽象节点必须反指 atom。
3. 抽象节点必须反指 source span。
4. 不允许生成无证据主题。
5. 抽象树应支持从全书主题下钻到段落证据。

---

### 8.8 阶段八：路径索引构建

输出：

```text
route_paths.jsonl
route_index.sqlite
```

索引对象：

```text
concept paths
argument paths
definition paths
figure paths
counterexample paths
chapter paths
source paths
```

要求：

1. 路径必须有入口节点。
2. 路径必须有终点证据。
3. 路径必须记录中间节点。
4. 路径必须记录选择理由。
5. 路径必须支持重新计算和修复。

---

### 8.9 阶段九：质量报告

输出：

```text
build_report.md
errors.jsonl
```

报告必须包含：

1. 页数。
2. 提取段落数。
3. 图片数量。
4. 表格数量。
5. source span 数量。
6. atom 数量。
7. route node 数量。
8. route edge 数量。
9. 无证据节点数量。
10. 无映射 source span 数量。
11. OCR 低置信区域。
12. 图像描述失败列表。
13. schema 校验错误。
14. provenance 覆盖率。
15. 推荐人工复核位置。

---

## 9. 查询流程标准

标准查询过程如下：

```text
user question
→ classify intent
→ find entry points
→ plan route
→ traverse nodes
→ inspect evidence
→ verify path
→ assemble answer
→ attach source references
```

### 9.1 问题意图分类

必须区分：

```text
definition_query
local_fact_query
global_synthesis_query
concept_trace_query
argument_trace_query
figure_query
comparison_query
counter_evidence_query
source_location_query
```

不同问题使用不同路由策略。

---

### 9.2 路由策略

#### local_reading

用于定位局部原文。

```text
question
→ concept/entity/section entry
→ nearest evidence nodes
→ source span
```

#### global_synthesis

用于全书级综合。

```text
question
→ book theme
→ community/topic nodes
→ representative atoms
→ evidence paths
```

#### concept_trace

用于追踪概念演化。

```text
concept
→ first occurrence
→ definition nodes
→ recurring mentions
→ changed usage
→ final synthesis
```

#### argument_trace

用于追踪论证链。

```text
claim
→ premises
→ evidence
→ examples
→ counterarguments
→ conclusion
```

#### figure_trace

用于图文互证。

```text
figure
→ caption
→ surrounding text
→ figure interpretation atom
→ related concepts
→ cited claims
```

#### counter_evidence

用于查找限制和反例。

```text
claim
→ contrast/refute/exception edges
→ ambiguous nodes
→ footnotes
→ appendices
→ source verification
```

---

## 10. 回答生成标准

后续 AI 生成回答时必须遵守：

1. 先走知识路径，再组织语言。
2. 不得只根据摘要回答。
3. 重要结论必须有 source span 支持。
4. 若证据不足，必须说明不足。
5. 若路径中包含 hypothesis edge，必须标记为推测。
6. 若问题需要全局综合，应返回多个路径的综合，而不是单一路径。
7. 若问题要求原文位置，应返回页码、Markdown anchor、bbox 或 asset ID。
8. 回答应能解释“为什么这些证据被选中”。

推荐回答内部结构：

```text
answer
supporting_paths
supporting_atoms
source_spans
figures
uncertainties
```

---

## 11. 质量验收标准

一个合格的知识路由 Skill / Agent 至少应满足以下指标。

### 11.1 Provenance 覆盖率

```text
source_mapped_atoms / total_atoms >= 0.98
```

至少 98% 的 atom 必须能回指原文。

---

### 11.2 无证据节点比例

```text
route_nodes_without_evidence / total_route_nodes <= 0.02
```

无证据节点不得超过 2%。
无证据节点只能处于 draft 或 hypothesis 状态。

---

### 11.3 图像映射完整度

```text
mapped_figures / extracted_figures >= 0.95
```

至少 95% 的图像应具备：

* asset path
* source page
* bbox 或页面区域
* description
* related source spans
* related route nodes

---

### 11.4 路径可解释率

对测试问题，返回路径中每一步都应有 reason。

```text
explained_steps / total_steps >= 0.95
```

---

### 11.5 证据闭环率

每个最终回答中的核心结论必须能追溯到 source span。

```text
claims_with_source / answer_claims >= 0.95
```

---

### 11.6 噪声控制

返回证据应尽量少而充分。

建议记录：

```text
evidence_precision
average_path_length
irrelevant_span_rate
redundant_span_rate
```

---

### 11.7 局部定位测试

系统必须能回答：

```text
某概念在哪些页出现？
某图解释了什么？
某论点的原文在哪里？
某章节的核心命题是什么？
某术语第一次出现在哪里？
```

---

### 11.8 全局综合测试

系统必须能回答：

```text
全书如何论证某主题？
某概念如何跨章节演化？
作者在哪些地方修正了前文观点？
哪些图像共同支持同一概念？
某论证链的前提、例子、结论分别在哪里？
```

---

## 12. 失败模式与禁止行为

系统必须显式防止以下失败模式：

### 12.1 Chunk 伪装成知识

错误：

```text
route_node = paragraph chunk
```

正确：

```text
route_node = claim / concept / argument / evidence
source_span = paragraph chunk
```

---

### 12.2 摘要替代证据

错误：

```text
根据章节摘要直接回答。
```

正确：

```text
章节摘要只用于定位；回答必须回到 source span。
```

---

### 12.3 图谱无来源

错误：

```text
concept A supports concept B
```

但无 source span。

正确：

```text
concept A supports claim B
evidence_spans = [...]
confidence = ...
```

---

### 12.4 路径不可解释

错误：

```text
返回三个相关节点，但不说明为什么。
```

正确：

```text
每一步路径都记录 action 和 reason。
```

---

### 12.5 混淆事实边和推测边

错误：

```text
related_to 被当成 supports 使用。
```

正确：

```text
hard / semantic / hypothesis 分层。
```

---

### 12.6 只做相似度检索

错误：

```text
embedding top-k → answer
```

正确：

```text
entry point → route planning → graph traversal → evidence inspection → source verification
```

---

## 13. Skill 行为规范

### 13.1 `SKILL.md` 必须声明

1. 本 skill 的目标。
2. 输入文件类型。
3. 输出文件结构。
4. 构建流程。
5. 查询流程。
6. schema 约束。
7. 质量门槛。
8. 失败处理策略。
9. 何时不应使用该 skill。
10. 后续 agent 如何调用路由工具。

---

### 13.2 Skill 必须提供两类能力

#### Build Mode

用于构建知识路由网络。

```text
build_book_route_network(input_file, output_dir, config)
```

#### Query Mode

用于查询已构建网络。

```text
query_book_route_network(question, route_index, mode)
```

---

### 13.3 Skill 必须可重复运行

要求：

1. 同一输入应生成稳定 ID。
2. 构建过程应可断点恢复。
3. 每个阶段应可单独重跑。
4. 修复不应破坏已有引用。
5. 输出应可 diff。

---

### 13.4 Skill 必须支持审计

每个模型生成内容应记录：

```text
model
prompt version
input source IDs
output schema version
timestamp
confidence
validation status
```

---

## 14. Agent 协议标准

后续 Agent 不直接读取全书，而是通过以下协议操作知识空间。

### 14.1 Agent 的基本循环

```text
1. Understand question
2. Select route mode
3. Find entry nodes
4. Plan route
5. Traverse graph/tree
6. Inspect evidence
7. Verify source
8. Expand or stop
9. Compose answer
10. Report uncertainty
```

---

### 14.2 Agent 的停止条件

满足以下条件之一可以停止路由：

1. 已找到最小充分证据集。
2. 路径继续扩展只会增加冗余。
3. 证据已经覆盖问题的主要子问题。
4. 达到预算上限。
5. 发现问题超出文档范围。
6. 发现证据冲突，需要报告冲突而不是继续扩展。

---

### 14.3 Agent 的扩展条件

以下情况必须继续扩展：

1. 只有摘要，没有 source span。
2. 只有单一证据，但问题要求全局综合。
3. 路径中包含 hypothesis edge。
4. 当前证据与问题只间接相关。
5. 发现反例或限制条件线索。
6. 图像和正文存在未解释关系。
7. 节点声明 `cannot_answer` 与问题相关。

---

## 15. 推荐配置

### 15.1 构建配置

```json
{
  "atom_granularity": "fine",
  "include_figures": true,
  "include_tables": true,
  "include_formulas": true,
  "build_structural_tree": true,
  "build_semantic_graph": true,
  "build_abstraction_tree": true,
  "build_argument_graph": true,
  "build_route_paths": true,
  "allow_hypothesis_edges": true,
  "require_source_for_semantic_edges": true,
  "min_confidence_for_verified_edge": 0.75
}
```

---

### 15.2 查询配置

```json
{
  "default_mode": "route_planning",
  "max_path_depth": 5,
  "max_evidence_spans": 12,
  "allow_hypothesis_edges": false,
  "require_source_verification": true,
  "prefer_minimal_sufficient_evidence": true,
  "return_route_explanation": true
}
```

---

## 16. 最小可行版本

MVP 可以只实现以下能力：

```text
1. PDF / EPUB → Markdown
2. 图片 / 表格提取与描述
3. source span 双向映射
4. atom 抽取
5. 章节树
6. 概念 / 命题图
7. route node / route edge
8. find_entry_points
9. inspect_evidence
10. jump_to_source
```

MVP 不必一开始实现：

```text
1. 完整自动反证搜索
2. 复杂逻辑推理
3. 多文档融合
4. 全自动 ontology 对齐
5. 高级 Personalized PageRank
6. 动态社区重构
```

但 MVP 必须保证：

```text
每个知识节点都能回到原文。
每个回答都能说明路径。
每个路径都能落到证据。
```

---

## 17. 成熟版本能力

成熟版本应增加：

1. 跨章节概念演化追踪。
2. 论证链抽取。
3. 反证与限制条件搜索。
4. 图文互证。
5. 多层社区摘要。
6. 查询时动态路径规划。
7. Agentic graph traversal。
8. 路径级缓存。
9. 人工修复界面。
10. 可视化知识地图。
11. 多书籍 / 多文档融合。
12. 版本化 route graph。
13. 可导出给其他 Agent 使用的工具接口。

---

## 18. 最终判定标准

一个 Skill / Agent 只有满足以下条件，才可被认为是真正的“知识路由网络”系统：

1. 它的基本检索结果是路径，而不是 chunk。
2. 它的基本知识单位是 atom，而不是段落。
3. 它的每个抽象节点都能回到原文。
4. 它同时拥有结构树、语义图和路径索引。
5. 它能区分事实关系、语义关系和推测关系。
6. 它能解释为什么沿这条路径找到这些证据。
7. 它能处理图像、表格、正文之间的映射。
8. 它能支持局部精读和全局综合。
9. 它能告诉用户证据不足或路径不可靠。
10. 它不会退化为 embedding top-k RAG。

最终标准句：

> 一个合格的长文知识路由 Skill / Agent，不是把书存进向量库，而是把书编译成一个可导航、可验证、可回溯、可执行的知识系统。
