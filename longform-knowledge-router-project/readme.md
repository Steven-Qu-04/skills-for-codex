# longform-knowledge-router-project 使用说明

`longform-knowledge-router` 是一个用于长文档知识图谱构建与读取的 Codex skill。它适合处理书籍、PDF、EPUB、DOCX、报告、论文集、文档文件夹等长篇材料，目标不是做普通 top-k chunk 检索，而是把长文档构造成一个可定位、可追溯、可验证的知识路由网络。

## 主要功能

该 skill 支持两种模式：

- `Construct Mode`：从源文档构建知识图谱/知识路由网络。
- `Read Mode`：基于已经构建好的知识图谱回答问题、追踪概念、定位原文、核验证据。

构建后的知识库通常包含：

- `book.md`：带锚点的正文 Markdown。
- `source_spans.jsonl`：可回指页码、锚点、原文片段的证据容器。
- `graph_patches.jsonl`：逐阅读帧产生的深读补丁。
- `atoms.jsonl`：原子知识单元。
- `route_nodes.jsonl` / `route_edges.jsonl`：知识路由节点与边。
- `route_graph.json` / `route_index.sqlite`：可查询的路由图和索引。
- `claim_registry.jsonl` / `concept_registry.jsonl`：命题与概念注册表。
- `repair_suggestions.jsonl`：无法可靠读取或需要修复的位置。

## 简单设计逻辑

这个 skill 的核心思想是：**长文档不是一堆可相似度检索的文本块，而是一个需要被路由、验证和引用的证据系统。**

它大致分为四层：

1. **证据层**
   段落、页码、锚点、图表、bbox、source span 都是证据容器。最终回答重要问题时，必须能回到这些证据。

2. **原子知识层**
   从证据中抽取最小知识单元，例如定义、命题、事实、例子、论据、限制条件、方法步骤等。

3. **路由图层**
   把概念、命题、论证、章节、证据之间的关系组织成 route nodes 和 route edges。边需要区分 hard / semantic / hypothesis，避免把推测当事实。

4. **查询路由层**
   回答问题时先找入口节点，再沿路径展开，最后回到 source spans 核验证据。输出应是 route path + evidence，而不是无序文本片段。

特别注意：真实构建必须经过 Manual Reading Gate / Deep Reader Agent Gate。脚本可以准备阅读帧、索引和模板，但不能替代 AI 对每个 frame 的实际阅读。

## 用法一：Construct Mode，构建知识图谱

当你有原始长文档，并希望生成知识图谱时，在 prompt 中明确三件事：

- skill 路径
- 源文件或源目录路径
- 目标输出目录

### Prompt 模板

```text
请使用以下 skill 的 Construct Mode 构建长文档知识图谱：

skill 路径：<longform-knowledge-router skill 路径>
源文件/源目录路径：<要处理的 PDF / EPUB / DOCX / Markdown / 文档目录路径>
目标输出目录：<知识图谱输出目录>

要求：
1. 按该 skill 的 Construct Mode 执行。
2. 先读取 SKILL.md 以及构建模式要求的 references 文档。
3. 运行自动准备流程，生成 source spans、reading frames、reading frame packets 等。
4. 在 Manual Reading Gate 后，按 Deep Reader Agent Gate 完成逐 frame 深读。
5. 生成并验证 v2 deep-reading artifacts。
6. 通过验证后 promote、integrate、extract atoms、build route graph、build route index。
7. 最终输出完整知识图谱，并运行 validate_build.py。
8. 不要用 heuristic-demo 结果冒充真实深读结果。
```

### 示例 Prompt

```text
请使用 longform-knowledge-router-project/longform-knowledge-router 这个 skill 的 Construct Mode，
为以下 PDF 构建长文档知识图谱：

源文件路径：E:\books\clinical_psychology.pdf
目标输出目录：E:\knowledge_graphs\clinical_psychology_graph

请严格按照该 skill 的 Construct Mode 流程执行：读取相关 references，完成自动准备流程，
在 Manual Reading Gate 后进行真实 deep reading，生成 v2 artifacts，验证、promote、integrate，
最后生成 route_index.sqlite、route_nodes.jsonl、route_edges.jsonl、atoms.jsonl、source_spans.jsonl，
并运行 validate_build.py。不要使用 heuristic-demo 作为真实构建结果。
```

## 用法二：Read Mode，读取/查询已有知识库

当知识图谱已经构建完成，需要基于它回答问题、追踪概念、定位证据时，使用 Read Mode。

在 prompt 中明确三件事：

- skill 路径
- 已构建知识库路径
- 具体任务要求

### Prompt 模板

```text
请使用以下 skill 的 Read Mode 读取已经构建好的知识图谱：

skill 路径：<longform-knowledge-router skill 路径>
知识库路径：<已经构建好的 output_dir，里面应包含 route_index.sqlite、source_spans.jsonl 等文件>
任务要求：<你的问题或分析任务>

要求：
1. 先读取该 skill 的 Read Mode 说明，以及 references/routing_protocol.md 和 references/route_scoring.md。
2. 使用 route_index.sqlite、route_nodes.jsonl、route_edges.jsonl、atoms.jsonl、source_spans.jsonl 等图谱产物。
3. 通过 route traversal 和 evidence verification 回答，不要把原文全文当普通文本重新检索。
4. 对重要结论给出 route path、source span、页码或 anchor 等证据。
5. 如果路径或证据不足，要说明不确定性或写出 repair suggestion。
```

### 示例 Prompt

```text
请使用 longform-knowledge-router-project/longform-knowledge-router 这个 skill 的 Read Mode，
读取以下知识库并回答问题：

知识库路径：E:\knowledge_graphs\clinical_psychology_graph
任务要求：这本书的主旨是什么？请给出支持该判断的 route paths 和 source spans。

请先读取 Read Mode 所需的 routing_protocol.md 和 route_scoring.md，
然后基于 route_index.sqlite、route_nodes.jsonl、route_edges.jsonl、atoms.jsonl、source_spans.jsonl 回答。
不要只做全文关键词检索，也不要只返回 top-k chunks。
```

## 常见 Read Mode 任务写法

```text
任务要求：解释某个概念在全书中的发展路径，并列出关键 source spans。
```

```text
任务要求：定位作者首次定义某个术语的位置，返回页码、anchor 和原文证据。
```

```text
任务要求：比较两个概念在书中的区别，并说明支持比较的 route paths。
```

```text
任务要求：找出某个论点的证据链、限制条件和可能的反例。
```

## 移植说明

独立移植时，复制整个目录即可：

```text
longform-knowledge-router-project/longform-knowledge-router
```

该目录内已经包含：

- `SKILL.md`
- `README.md`
- `requirements.txt`
- `references/`
- `references/read_agent_atandard.md`
- `scripts/`
- `assets/`
- `agents/`

推荐目标环境安装：

```bash
python -m pip install -r longform-knowledge-router/requirements.txt
```

其中 `PyMuPDF` 用于真实 PDF 文本解析。若缺失该依赖，PDF 解析会退化为原始字节读取，通常不适合正式构建。



