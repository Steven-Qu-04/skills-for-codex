# Skills for Codex

这个仓库用于保存和维护 Codex 可使用的本地 skills。每个 skill 通常是一个独立目录，包含 `SKILL.md`、脚本、参考文档、资源文件和必要的辅助配置，供 Codex 在特定任务中按需读取和执行。

当前项目的目标是把可复用的工作流沉淀成结构化 skill，让 Codex 在处理复杂任务时不只依赖临时 prompt，而是可以遵循稳定的流程、产物约定和验证规则。

## 现有 Skill

### longform-knowledge-router

路径：

```text
longform-knowledge-router-project/longform-knowledge-router
```

`longform-knowledge-router` 是一个面向长文档的知识路由 skill，适合处理书籍、PDF、EPUB、DOCX、报告、论文集和文档目录等材料。

它的核心目的不是做普通的 top-k 文本块检索，而是把长文档构造成可定位、可追溯、可验证的知识路由网络。构建后，Codex 可以基于 route graph、source spans、atoms、route index 等产物回答问题、追踪概念、定位原文证据和核验结论。

该 skill 主要包含三种模式：

- `Construct Mode`：从原始长文档构建知识图谱/知识路由网络。
- `Read Mode`：基于已经构建好的知识库进行查询、解释、比较、证据追踪和结论核验。
- `Arrange Mode`：编排多个已经构建好的知识库，生成跨知识库索引和可验证的跨库证据路径。

典型产物包括：

- `book.md`：带锚点的正文 Markdown。
- `source_spans.jsonl`：可回指页码、锚点和原文片段的证据容器。
- `atoms.jsonl`：原子知识单元。
- `route_nodes.jsonl` / `route_edges.jsonl`：知识路由节点与边。
- `route_graph.json` / `route_index.sqlite`：可查询的路由图和索引。
- `claim_registry.jsonl` / `concept_registry.jsonl`：命题与概念注册表。

新增的跨库编排产物包括：

- `kb_registry.jsonl`：记录可参与编排的子知识库。
- `alignment_candidates.jsonl`：跨库候选对齐关系，需验证后才能成为正式跨库边。
- `cross_edges.jsonl` / `cross_evidence_paths.jsonl`：经过验证的跨库关系和证据路径。
- `cross_route_index.sqlite`：用于跨库查询、比较、互证和综合的索引。

`Arrange Mode` 不会合并多个子知识库的全文或 route graph，而是在它们之上建立桥接层。跨库回答必须回到 `cross_evidence_path`、child verified path 和 child source span；不能只根据 cross node summary、semantic payload 或候选对齐关系下结论。

常用跨库构建流程：

```bash
python scripts/discover_kbs.py --workspace <workspace_dir> --output-dir <arrange_output>
python scripts/build_alignment_candidates.py --kb-registry <arrange_output>/kb_registry.jsonl --output-dir <arrange_output>
python scripts/query_child_kbs.py --alignment-candidates <arrange_output>/alignment_candidates.jsonl --kb-registry <arrange_output>/kb_registry.jsonl --output-dir <arrange_output>
python scripts/verify_cross_edges.py --alignment-candidates <arrange_output>/alignment_candidates.jsonl --cross-evidence-paths <arrange_output>/cross_evidence_paths.jsonl --output-dir <arrange_output>
python scripts/build_cross_route_index.py --cross-edges <arrange_output>/cross_edges.jsonl --cross-evidence-paths <arrange_output>/cross_evidence_paths.jsonl --kb-registry <arrange_output>/kb_registry.jsonl --output-dir <arrange_output>
python scripts/validate_arrange.py --arrange-output <arrange_output> --profile arrange_skeleton
```

跨库读取示例：

```bash
python scripts/query_route.py --question "不同知识库如何处理同一概念？" --scope cross_kb --cross-index <arrange_output>/cross_route_index.sqlite --kb-registry <arrange_output>/kb_registry.jsonl --mode cross_synthesis --session-dir <query_session_dir>
python scripts/score_paths.py --route-session <query_session_dir>/route_session.json --candidate-paths <query_session_dir>/candidate_cross_paths.jsonl --mode cross_synthesis
python scripts/verify_evidence.py --answer <query_session_dir>/answer.json --route-session <query_session_dir>/route_session.json --cross-edges <arrange_output>/cross_edges.jsonl --cross-evidence-paths <arrange_output>/cross_evidence_paths.jsonl
```

更多使用说明可参考：

```text
longform-knowledge-router-project/readme.md
```
