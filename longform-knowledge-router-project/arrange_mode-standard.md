
# Arrange Mode Technical Standard

文件建议位置：`references/arrange_protocol.md`
版本：v0.1-freeze-extension
适用范围：Longform Knowledge Router Skill 的跨知识库编排模式
核心目标：当工作目录中存在多个已经构建好的知识库时，生成一个跨知识库的深度知识交互索引，使后续 AI 能够跨书籍、跨报告、跨档案地比较、互证、追踪、综合和定位原文证据。

---

## 1. 模式定位

Longform Knowledge Router Skill 增加第三种运行模式：

```text
Construct Mode：从原始长文构建单个知识库
Read Mode：读取一个或多个已构建知识网络并生成问题相关路径
Arrange Mode：编排多个已构建知识库，生成跨知识库知识索引
```

Arrange Mode 的目标不是把每本书变成一个独立大节点，也不是简单合并多个 `route_graph.json`。它应构建一个跨知识库的深度交互网络，使不同知识库中的概念、命题、定义、论证、方法、图像解释和证据路径能够发生关系。

一句话目标：

> 不把多本书排成书架，而是把多本书的知识编织成可验证的思想网络。

---

## 2. 非目标

Arrange Mode 不应被设计成：

1. 多个知识库的简单目录。
2. 每本书一个节点的粗粒度关系图。
3. 多个 `route_graph.json` 的机械拼接。
4. 多个向量库的统一 top-k 检索。
5. 只基于标题、摘要、关键词或 embedding 相似度的聚类。
6. 无证据来源的跨书观点总结。
7. 把分歧强行消解为单一结论的融合器。

Arrange Mode 必须保留来源差异、作者立场、证据边界和冲突关系。

---

## 3. 核心设计哲学

### 3.1 先联邦，后融合

每个已构建知识库都是一个独立、可查询、可验证的子网络。Arrange Mode 不应直接吞并所有子图，而应先建立联邦式编排关系。

```text
child_kb = 可独立查询的知识网络
arrange_index = 跨知识库的编排层
```

子知识库继续保留自己的：

```text
source_spans
atoms
route_nodes
route_edges
route_graph
route_index
figures
book.md
```

Arrange Mode 只保存跨库关系、跨库路径和对子库证据的引用。

---

### 3.2 跨库节点不是书籍节点，而是知识节点

错误做法：

```text
Book A → related_to → Book B
```

正确做法：

```text
Book A 的 Concept X
→ contrasts_with / extends / refutes / aligns_with
→ Book B 的 Claim Y
→ 双侧 evidence paths
```

Arrange Mode 的核心对象应是：

```text
concept
definition
claim
argument
method
example
counterexample
figure_interpretation
evidence_path
```

不是整本书。

---

### 3.3 对齐不等于合并

跨库关系必须区分：

```text
same_as
alias_of
near_equivalent
broader_than
narrower_than
overlaps_with
contrasts_with
refutes
extends
qualifies
independently_supports
```

只有在证据强、边界一致、语义等价时，才允许建立 `same_as` 或 canonical object。
大多数跨库关系应保留为 bridge edge，而不是强行合并节点。

---

### 3.4 分歧是一等公民

如果不同知识库对同一问题存在不同定义、不同论证、不同适用范围或相反结论，Arrange Mode 不应把它们压缩成一个统一答案。

它应显式记录：

```text
conflict
contrast
qualification
scope difference
method difference
evidence difference
author/source-specific position
```

跨库索引不仅要发现共识，也要发现分歧。

---

### 3.5 verified cross-edge 必须有双侧证据

任何 verified 跨库边都必须同时具备：

```text
source side verified path
target side verified path
cross-edge explanation
cross-edge verification report
```

如果只有一侧证据，或仅来自模型推断，应标记为：

```text
one_sided
hypothesis
needs_review
```

---

### 3.6 Arrange Mode 必须能够深入查询子知识库

Arrange Mode 不能只读取每个知识库的摘要、报告或 top-level payload。
当跨库关系需要确认时，必须调用子知识库的 Read Mode：

```text
candidate cross relation
→ query child KB A
→ query child KB B
→ inspect verified paths
→ inspect source spans if needed
→ verify cross-edge
```

也就是说：

> Arrange Mode 是跨库编排器；每个子知识库是可被调用的证据代理。

---

### 3.7 跨库索引保存桥梁，不复制全文

Arrange Mode 不复制全部子知识库内容。它只保存：

```text
kb registry
cross registries
alignment records
cross nodes
cross edges
cross evidence paths
cross route templates
cross route index
verification reports
```

所有原文证据仍由各自 child KB 持有。

---

## 4. 模式输入与输出

### 4.1 输入

Arrange Mode 输入为一个 workspace，其中包含多个已经构建完成的知识库目录。

每个 child KB 至少应包含：

```text
book.md
source_spans.jsonl
atoms.jsonl
route_nodes.jsonl
route_edges.jsonl
route_graph.json
route_index.sqlite
route_path_templates.jsonl
build_report.md
```

可选增强输入：

```text
figures.jsonl
figure_readings.jsonl
figure_atlas.json
figure_routes.jsonl
route_communities.jsonl
route_reports.jsonl
concept_registry.jsonl
claim_registry.jsonl
semantic_payloads
```

### 4.2 输出

Arrange Mode 输出到：

```text
arrange_output/
├── arrange_manifest.json
├── kb_registry.jsonl
├── cross_concept_registry.jsonl
├── cross_claim_registry.jsonl
├── cross_argument_registry.jsonl
├── alignment_candidates.jsonl
├── rejected_alignments.jsonl
├── cross_nodes.jsonl
├── cross_edges.jsonl
├── cross_evidence_paths.jsonl
├── cross_communities.jsonl
├── cross_route_templates.jsonl
├── cross_route_index.sqlite
├── arrange_sessions.jsonl
├── arrange_report.md
├── repair_suggestions.jsonl
└── errors.jsonl
```

---

## 5. Arrange Mode 主流程

```text
workspace
→ discover child KBs
→ validate child KBs
→ build kb_registry
→ load high-level registries / payloads / route reports
→ generate alignment candidates
→ group candidates by concept / claim / argument / method / figure role
→ query child KBs for evidence where needed
→ verify candidate alignments and cross-edges
→ build cross nodes and cross edges
→ build cross evidence paths
→ build cross communities and route templates
→ build cross route index
→ validate arrange output
→ write arrange_report.md
```

---

## 6. 核心对象

## 6.1 KB Registry

记录每个子知识库的身份、路径、状态和可查询能力。

```json
{
  "kb_id": "kb_book_a",
  "kb_path": "./book_a/output",
  "title": "",
  "source_type": "book | report | archive | paper_collection | manual | other",
  "domain": "",
  "build_profile": "mvp2 | mature",
  "available_artifacts": {
    "route_index": true,
    "route_graph": true,
    "route_reports": false,
    "figure_atlas": false
  },
  "read_mode_endpoint": {
    "route_index": "route_index.sqlite",
    "route_graph": "route_graph.json"
  },
  "validation_status": "valid | partial | invalid | needs_review"
}
```

规则：

1. 无有效 `route_index.sqlite` 的 KB 不得作为 verified child KB。
2. build profile 低于 MVP-2 的 KB 可进入 registry，但只能参与 limited arrange。
3. invalid KB 不得生成 verified cross-edge。

---

## 6.2 Alignment Candidate

Alignment Candidate 是跨库候选关系，不是正式跨库边。

```json
{
  "alignment_candidate_id": "ac_<hash>",
  "candidate_type": "concept | claim | argument | method | example | figure_interpretation",
  "source": {
    "kb_id": "kb_book_a",
    "object_type": "route_node | atom | claim | concept",
    "object_id": ""
  },
  "target": {
    "kb_id": "kb_book_b",
    "object_type": "route_node | atom | claim | concept",
    "object_id": ""
  },
  "proposed_relation": "same_as | near_equivalent | contrasts_with | refutes | extends | qualifies | supports",
  "basis": {
    "label_similarity": 0.0,
    "payload_similarity": 0.0,
    "structural_similarity": 0.0,
    "shared_aliases": [],
    "shared_evidence_type": [],
    "model_rationale": ""
  },
  "status": "candidate | verified | rejected | needs_child_query"
}
```

规则：

1. candidate 可以由 label、payload、alias、registry、route report、embedding 或模型判断提出。
2. candidate 不得直接进入最终 cross graph。
3. candidate 必须经过 child KB evidence query 或明确标记为 hypothesis。

---

## 6.3 Cross Node

Cross Node 表示跨库层面的概念、命题、论证或主题聚合点。

```json
{
  "cross_node_id": "xnode_<hash>",
  "type": "cross_concept | cross_claim | cross_argument | cross_method | cross_theme | cross_figure_role",
  "title": "",
  "summary": "",
  "member_objects": [
    {
      "kb_id": "kb_book_a",
      "object_type": "route_node | atom | claim | path",
      "object_id": "",
      "role": "primary | variant | opposing | supporting | qualifying"
    }
  ],
  "semantic_payload": {},
  "can_answer": [],
  "cannot_answer": [],
  "verification_status": "verified | partial | hypothesis | needs_review"
}
```

规则：

1. Cross Node 不替代 child KB 原节点。
2. Cross Node 必须保存 member objects。
3. 若 member objects 存在语义分歧，summary 必须保留分歧，不得写成单一结论。

---

## 6.4 Cross Edge

Cross Edge 是跨库知识交互关系。

```json
{
  "cross_edge_id": "xedge_<hash>",
  "source_kb_id": "kb_book_a",
  "target_kb_id": "kb_book_b",
  "source_object": {
    "type": "concept | claim | route_node | atom | path",
    "id": ""
  },
  "target_object": {
    "type": "concept | claim | route_node | atom | path",
    "id": ""
  },
  "relation_type": "same_as | alias_of | near_equivalent | broader_than | narrower_than | overlaps_with | extends | applies_to | supports | independently_supports | refutes | contrasts_with | qualifies | uses_same_example | uses_same_method | shares_evidence_type | historically_precedes | methodologically_depends_on",
  "edge_class": "hard | semantic | hypothesis | alignment | dialectical | comparative",
  "explanation": "",
  "source_evidence_paths": [],
  "target_evidence_paths": [],
  "verification_status": "verified | one_sided | hypothesis | needs_review | rejected",
  "confidence": 0.0,
  "provenance": {
    "child_kb_paths": [],
    "source_spans": [],
    "figures": []
  }
}
```

规则：

1. `verified` cross edge 必须有双侧 verified child paths。
2. `same_as` 必须有强对齐证据，不得只靠名称相同。
3. `refutes`、`contrasts_with`、`qualifies` 必须保留双方原始立场。
4. `hypothesis` edge 可用于探索，但不得作为最终回答证据。

---

## 6.5 Cross Evidence Path

Cross Evidence Path 是跨库查询和回答的基本证据结构。

```json
{
  "cross_evidence_path_id": "xep_<hash>",
  "question_or_intent": "",
  "cross_steps": [
    {
      "step_type": "enter_cross_node | follow_cross_edge | query_child_kb | inspect_child_path | verify_source_span",
      "kb_id": "",
      "object_id": "",
      "reason": ""
    }
  ],
  "child_paths": [
    {
      "kb_id": "kb_book_a",
      "route_session_id": "",
      "verified_path_id": "",
      "source_spans": [],
      "figures": []
    }
  ],
  "cross_edges": [],
  "answer_affordance": "compare | synthesize | trace | locate | verify | contrast",
  "verification_status": "verified | partial | hypothesis | needs_review"
}
```

规则：

1. 跨库回答必须优先返回 cross evidence path，而不是无序 child snippets。
2. 每个 child path 必须来自 child KB Read Mode。
3. 如果只存在 cross edge 而无 child path，不能进入 verified answer。

---

## 7. 跨库关系类型

### 7.1 对齐类

```text
same_as
alias_of
near_equivalent
broader_than
narrower_than
overlaps_with
```

用途：概念、定义、方法、术语的跨库对齐。

### 7.2 辩证类

```text
refutes
contrasts_with
qualifies
limits
reframes
```

用途：记录观点冲突、限定、修正、不同适用范围。

### 7.3 支持类

```text
supports
independently_supports
extends
applies_to
uses_same_example
uses_same_method
shares_evidence_type
```

用途：记录不同知识库之间的互证、扩展、方法复用。

### 7.4 历史 / 方法关系

```text
historically_precedes
methodologically_depends_on
responds_to
develops_from
```

用途：处理思想史、理论演化、方法传承。

---

## 8. Arrange Session

Arrange Mode 必须像 Read Mode 一样保留 session。

```json
{
  "arrange_session_id": "as_<hash>",
  "workspace": "",
  "kb_ids": [],
  "task": "build_cross_index | update_cross_index | verify_cross_edges | add_new_kb",
  "active_alignment_groups": [],
  "queried_kbs": [],
  "candidate_alignments": [],
  "verified_cross_edges": [],
  "rejected_cross_edges": [],
  "open_conflicts": [],
  "repair_suggestions": [],
  "budget_used": {
    "child_kb_queries": 0,
    "paths_verified": 0,
    "source_spans_inspected": 0
  },
  "status": "running | complete | needs_review | failed"
}
```

用途：

1. 记录哪些 KB 被查询。
2. 记录为什么生成某个跨库关系。
3. 记录 rejected alignments，避免重复误合并。
4. 支持后续新增知识库时增量更新。

---

## 9. Child KB Query Protocol

Arrange Mode 生成 verified cross-edge 前，必须能够调用子知识库 Read Mode。

### 9.1 查询子库的触发条件

以下情况必须查询 child KB：

```text
same_as candidate
refutes / contrasts_with candidate
extends / qualifies candidate
high-impact cross claim
low-confidence alignment
only label-based candidate
cross answer depends on this relation
```

### 9.2 查询输入

```json
{
  "child_kb_id": "kb_book_a",
  "question": "",
  "mode": "local_reading | concept_trace | argument_trace | source_verification",
  "target_objects": [],
  "required_evidence_types": ["definition", "claim", "example", "counterexample", "figure", "source_span"]
}
```

### 9.3 查询输出

必须返回：

```text
route_session
verified_paths
source_spans
supporting_atoms
figures
uncertainties
```

规则：

1. Arrange Mode 不得直接读 child KB 原始全文。
2. Arrange Mode 只能通过 child KB Read Mode 获取 verified paths。
3. 必要时可让 child KB Read Mode 执行 `source_verification`，回到 source span、Markdown anchor、bbox 或 figure asset。
4. 子库查询失败时，cross-edge 降级为 `needs_review` 或 `hypothesis`。

---

## 10. Cross Evidence Verification

跨库验证分为四级：

```text
alignment verification
child path verification
cross-edge verification
cross-answer verification
```

### 10.1 Alignment Verification

检查：

1. 是否只基于标题或标签。
2. 是否存在同名异义。
3. 是否存在近义但不同范围。
4. 是否需要保留为 `near_equivalent` 而不是 `same_as`。

### 10.2 Child Path Verification

检查：

1. child path 是否来自 child KB Read Mode。
2. child path 是否 verified。
3. child path 是否有 source spans。
4. child path 是否使用了 payload / gist 作为证据。

### 10.3 Cross-Edge Verification

检查：

1. 双侧证据是否都存在。
2. 关系类型是否被双侧证据支持。
3. 是否应从 `same_as` 降级为 `near_equivalent` 或 `overlaps_with`。
4. 是否应从 `supports` 改为 `qualifies`、`contrasts_with` 或 `independently_supports`。

### 10.4 Cross-Answer Verification

检查：

1. 回答中的每个核心结论是否至少有一个 cross evidence path。
2. 涉及多库比较时，是否呈现双方来源。
3. 涉及冲突时，是否保留冲突而不是消解冲突。
4. 是否有单侧证据被误写成双侧结论。

---

## 11. Arrange Mode 输出质量门槛

```text
verified_cross_edges_with_two_sided_evidence / verified_cross_edges >= 0.95
same_as_edges_with_strong_alignment_evidence / same_as_edges = 1.0
cross_edges_without_child_path / cross_edges <= 0.05
rejected_alignment_logged / rejected_alignment_candidates >= 0.95
cross_answers_with_cross_evidence_path / cross_answers >= 0.95
payload_used_as_cross_evidence = 0
```

---

## 12. Arrange Mode 失败模式

### 12.1 书籍节点化

错误：

```text
Book A related_to Book B
```

正确：

```text
Claim A in Book A contrasts_with Claim B in Book B
```

---

### 12.2 标签合并

错误：

```text
两个库都有“记忆”一词，因此 same_as
```

正确：

```text
先查定义、上下文、适用范围和证据路径，再决定 same_as / near_equivalent / overlaps_with
```

---

### 12.3 分歧被消解

错误：

```text
两本书观点不同，系统总结成折中观点
```

正确：

```text
保留两个观点、双方证据、冲突边和适用范围
```

---

### 12.4 摘要替代双侧证据

错误：

```text
根据 route_report 判断 A 支持 B
```

正确：

```text
route_report 只能作为导航入口；verified cross-edge 必须回到 child verified paths
```

---

### 12.5 跨库索引复制全部子图

错误：

```text
把所有 child atoms / nodes / edges 全部复制进 cross index
```

正确：

```text
cross index 保存跨库节点、跨库边、证据路径和 child references
```

---

## 13. Script Interface

建议新增脚本：

```text
discover_kbs.py
build_alignment_candidates.py
query_child_kbs.py
verify_cross_edges.py
build_cross_route_index.py
validate_arrange.py
```

### 13.1 discover_kbs.py

```bash
python scripts/discover_kbs.py --workspace <workspace_dir> --output-dir <arrange_output>
```

输出：

```text
arrange_manifest.json
kb_registry.jsonl
```

### 13.2 build_alignment_candidates.py

```bash
python scripts/build_alignment_candidates.py --kb-registry <kb_registry.jsonl> --output-dir <arrange_output>
```

输出：

```text
alignment_candidates.jsonl
cross_concept_registry.jsonl
cross_claim_registry.jsonl
```

### 13.3 query_child_kbs.py

```bash
python scripts/query_child_kbs.py --alignment-candidates <alignment_candidates.jsonl> --kb-registry <kb_registry.jsonl> --output-dir <arrange_output>
```

输出：

```text
child_query_sessions.jsonl
cross_evidence_paths.jsonl
```

### 13.4 verify_cross_edges.py

```bash
python scripts/verify_cross_edges.py --alignment-candidates <alignment_candidates.jsonl> --cross-evidence-paths <cross_evidence_paths.jsonl> --output-dir <arrange_output>
```

输出：

```text
cross_edges.jsonl
rejected_alignments.jsonl
repair_suggestions.jsonl
```

### 13.5 build_cross_route_index.py

```bash
python scripts/build_cross_route_index.py --cross-edges <cross_edges.jsonl> --cross-evidence-paths <cross_evidence_paths.jsonl> --output-dir <arrange_output>
```

输出：

```text
cross_nodes.jsonl
cross_communities.jsonl
cross_route_templates.jsonl
cross_route_index.sqlite
```

### 13.6 validate_arrange.py

```bash
python scripts/validate_arrange.py --arrange-output <arrange_output> --profile arrange_mvp | arrange_mature
```

---

# Read Mode Adaptation Standard

## 14. Read Mode 适配目标

加入 Arrange Mode 后，Read Mode 必须支持两类查询对象：

```text
single_kb：单个知识库
cross_kb：跨知识库索引
```

Read Mode 不再只能读取一个 `route_index.sqlite`，还应能读取：

```text
cross_route_index.sqlite
kb_registry.jsonl
cross_edges.jsonl
cross_evidence_paths.jsonl
```

---

## 15. Read Mode 新增输入

Read Mode 输入扩展为：

```text
--scope single_kb | cross_kb | auto
--kb <kb_id>
--workspace <workspace_dir>
--cross-index <cross_route_index.sqlite>
--kb-registry <kb_registry.jsonl>
```

示例：

```bash
python scripts/query_route.py \
  --question "不同书中如何理解记忆与身份的关系？" \
  --scope cross_kb \
  --cross-index arrange_output/cross_route_index.sqlite \
  --kb-registry arrange_output/kb_registry.jsonl \
  --mode cross_synthesis
```

---

## 16. Read Mode 新增意图分类

新增 query intents：

```text
cross_concept_trace_query
cross_claim_comparison_query
cross_argument_comparison_query
cross_evidence_synthesis_query
cross_conflict_query
cross_source_location_query
cross_method_comparison_query
cross_figure_trace_query
```

---

## 17. Read Mode 新增路由模式

```text
cross_local_reading
cross_synthesis
cross_concept_trace
cross_argument_trace
cross_conflict_trace
cross_evidence_verification
cross_source_verification
```

---

## 18. Cross Read Session

Read Mode 对跨库查询必须输出 cross route session。

```json
{
  "route_session_id": "xrs_<hash>",
  "scope": "cross_kb",
  "question": "",
  "intent": "cross_claim_comparison_query",
  "active_cross_nodes": [],
  "visited_cross_edges": [],
  "queried_child_kbs": [],
  "child_route_sessions": [],
  "candidate_cross_paths": [],
  "verified_cross_paths": [],
  "rejected_cross_paths": [],
  "open_conflicts": [],
  "uncertainties": [],
  "stop_reason": "",
  "budget_used": {
    "cross_nodes_read": 0,
    "cross_edges_followed": 0,
    "child_kb_queries": 0,
    "source_spans_inspected": 0
  }
}
```

---

## 19. Cross Read 主流程

```text
user question
→ classify cross intent
→ search cross_route_index
→ find cross entry nodes / edges
→ inspect cross evidence paths
→ query child KBs if needed
→ verify child paths
→ compare / synthesize / contrast
→ assemble answer with cross evidence paths
→ attach child source references
```

---

## 20. Read Mode 的跨库证据规则

跨库回答必须引用：

```text
cross_evidence_path
child verified path
child source span
```

不得只引用：

```text
cross_node summary
cross_edge explanation
semantic_payload
route_report
```

硬规则：

1. 如果回答涉及两个知识库的比较，必须至少有两个 child evidence paths。
2. 如果回答涉及冲突，必须呈现双方证据。
3. 如果只有一侧证据，应明确标注为 one-sided。
4. 如果 cross-edge 是 hypothesis，不得写成确定结论。
5. 如果 cross_route_index 没有足够证据，Read Mode 必须触发 child KB query 或报告证据不足。

---

## 21. Read Mode 输出结构更新

跨库查询输出：

```json
{
  "answer": "",
  "scope": "cross_kb",
  "supporting_cross_paths": [],
  "supporting_child_paths": [],
  "source_spans_by_kb": {
    "kb_book_a": [],
    "kb_book_b": []
  },
  "figures_by_kb": {},
  "cross_edges_used": [],
  "conflicts": [],
  "one_sided_claims": [],
  "uncertainties": [],
  "verification_report": {}
}
```

---

## 22. Cross Answer Verification

`verify_evidence.py` 必须增加：

```text
verify_cross_path_grounding
verify_child_path_grounding
verify_cross_edge_status
verify_two_sided_evidence
verify_conflict_preserved
verify_no_payload_as_cross_evidence
```

检查规则：

1. cross answer 的每个核心 claim 是否有 cross evidence path。
2. cross evidence path 是否包含 child verified paths。
3. child verified paths 是否能回到 source spans。
4. conflict 是否保留双方立场。
5. hypothesis cross edge 是否被误用为 verified edge。
6. payload / report 是否被误用为最终证据。

---

## 23. Read Mode 适配后的失败模式

### 23.1 跨库 top-k 退化

错误：

```text
在所有子库里 top-k 检索，然后拼答案
```

正确：

```text
cross_route_index → cross evidence path → child verified paths → source spans
```

### 23.2 跨库摘要替代证据

错误：

```text
根据 cross_node summary 回答
```

正确：

```text
summary 只用于导航，最终回答必须引用 child source spans
```

### 23.3 单侧证据冒充比较结论

错误：

```text
只查了 Book A，就说 Book A 与 Book B 不同
```

正确：

```text
必须查双方；否则标记 one_sided
```

### 23.4 冲突被过度综合

错误：

```text
两个知识库观点冲突，回答成一个折中总结
```

正确：

```text
保留冲突、双方证据、适用范围和不确定性
```

---

## 24. Arrange Mode 与 Read Mode 的最终关系

Arrange Mode 负责：

```text
发现跨库关系
验证跨库边
构建 cross route index
记录跨库证据路径
```

Read Mode 负责：

```text
读取 cross route index
沿跨库路径查询
必要时调用 child KB
生成带双侧证据的跨库回答
```

最终原则：

> Arrange Mode 建桥，Read Mode 走桥；桥的两端必须落到各自知识库的原文证据。
