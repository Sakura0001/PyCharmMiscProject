# Online Modify XMind Scenario Markdown Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the RDS MySQL 8.0.45 V3 XMind into one complete, scenario-first Markdown document whose 48 scenarios explicitly include prerequisites, coverage-factor scope, observation points, execution, acceptance, and source traceability.

**Architecture:** A small standard-library Python generator will read `content.json` directly from the XMind ZIP, reuse the existing V2 taxonomy and V1 scenario definitions, merge hand-authored scenario policies, and render a deterministic Markdown document. A separate verifier will validate scenario sections, source counts, factor coverage, traceability, placeholders, and source-file immutability before the artifact is delivered.

**Tech Stack:** Python 3 standard library (`zipfile`, `json`, `hashlib`, `re`, `pathlib`, `unittest`), Markdown, existing XMind JSON and existing taxonomy/scenario Python data.

---

## File map

- Create `.codex_tmp/online_modify_xmind_20260910_v4_md/scenario_policies.py`: shared vocabulary and customized policies for SC01–SC48.
- Create `.codex_tmp/online_modify_xmind_20260910_v4_md/xmind_model.py`: read-only XMind parsing and normalized topic/scenario models.
- Create `.codex_tmp/online_modify_xmind_20260910_v4_md/render_markdown.py`: deterministic scenario-first Markdown renderer.
- Create `.codex_tmp/online_modify_xmind_20260910_v4_md/verify_markdown.py`: structural, traceability, count, placeholder, and hash verification.
- Create `.codex_tmp/online_modify_xmind_20260910_v4_md/test_scenario_markdown.py`: standard-library unit tests for policies, parsing, rendering, and validation.
- Create `.codex_tmp/online_modify_xmind_20260910_v4_md/verification.json`: machine-readable verification evidence.
- Create `outputs/online_modify_xmind_20260910_v3/RDS_MySQL_8.0.45_测试计划_V4_场景化完整覆盖版.md`: final user-facing artifact.

The existing XMind and V1–V3 generation sources remain read-only.

### Task 1: Define the scenario policy contract and all 48 policy records

**Files:**

- Create: `.codex_tmp/online_modify_xmind_20260910_v4_md/scenario_policies.py`
- Create: `.codex_tmp/online_modify_xmind_20260910_v4_md/test_scenario_markdown.py`

- [ ] **Step 1: Write policy-contract tests that fail before the module exists**

Create tests that require exactly SC01–SC48 and reject incomplete policy records:

```python
import unittest

from scenario_policies import FACTOR_CATEGORIES, SCENARIO_POLICIES


class ScenarioPolicyTests(unittest.TestCase):
    def test_all_scenarios_have_complete_policies(self):
        expected = {f"SC{i:02d}" for i in range(1, 49)}
        self.assertEqual(expected, set(SCENARIO_POLICIES))
        required = {
            "goal", "risk", "prerequisites", "factor_scopes",
            "observation_points", "acceptance_additions",
        }
        for scene_id, policy in SCENARIO_POLICIES.items():
            self.assertEqual(required, set(policy), scene_id)
            self.assertGreaterEqual(len(policy["prerequisites"]), 4, scene_id)
            self.assertGreaterEqual(len(policy["observation_points"]), 5, scene_id)
            self.assertEqual(set(FACTOR_CATEGORIES), set(policy["factor_scopes"]), scene_id)
            for observation in policy["observation_points"]:
                self.assertEqual({"object", "evidence", "decision"}, set(observation), scene_id)
                self.assertTrue(all(str(value).strip() for value in observation.values()), scene_id)

    def test_scope_values_are_explicit(self):
        allowed = {"全部覆盖", "指定覆盖", "边界覆盖", "专属子运行", "不适用"}
        for scene_id, policy in SCENARIO_POLICIES.items():
            for category, scope in policy["factor_scopes"].items():
                self.assertIn(scope["requirement"], allowed, (scene_id, category))
                self.assertTrue(scope["range"].strip(), (scene_id, category))
                self.assertTrue(scope["strategy"].strip(), (scene_id, category))
```

- [ ] **Step 2: Run the focused tests and confirm the expected import failure**

Run:

```bash
cd .codex_tmp/online_modify_xmind_20260910_v4_md
python3 -m unittest -v test_scenario_markdown.ScenarioPolicyTests
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scenario_policies'`.

- [ ] **Step 3: Implement the policy schema and shared coverage vocabulary**

Define these nine factor categories exactly:

```python
FACTOR_CATEGORIES = (
    "环境与功能范围",
    "表结构、存储与物理状态",
    "列类型、属性与非目标列",
    "索引、约束与对象依赖",
    "数据值、规模与分布",
    "ALTER 语法、算法、锁与同句动作",
    "并发、事务、DDL 阶段与 row log",
    "主备、故障、恢复与客户端",
    "结构、数据、索引、性能与交付判定",
)


def scope(requirement, value_range, strategy):
    return {
        "requirement": requirement,
        "range": value_range,
        "strategy": strategy,
    }
```

Use `全部覆盖` when a scene owns all compatible values from the global factor catalog; use `指定覆盖`, `边界覆盖`, or `专属子运行` for constrained mechanisms; use `不适用` only with a concrete reason. “全部覆盖” always means all applicable values, not a Cartesian product.

- [ ] **Step 4: Fill SC01–SC48 with customized policy content**

Build every record explicitly. Apply these family-level responsibilities, then add scene-specific details from its title, original conditions, source test points, and mandatory variants:

| Scenes | Primary factor responsibility | Required observation emphasis |
|---|---|---|
| SC01–SC10 | all compatible table forms, relevant index roles, complete type/value boundary sets | algorithm/lock, online writes, exact value conversion, metadata and replica results |
| SC11–SC18 | all compatible index forms; MVI/FULLTEXT/SPATIAL/generated/function indexes in dedicated subruns | index build/maintenance, access paths, constraints, dependency metadata |
| SC19–SC24 | all compatible parent/child/partition table forms and relationship graphs | intermediate constraint state, routing, cascades, atomic rejection |
| SC25–SC30 | complete applicable ALTER entry points and same-statement action classes | parse/prepare/eligibility/execute error stage and statement atomicity |
| SC31–SC37 | boundary event sequences, transaction outcomes, DDL phases, row-log and uniqueness interactions | stage evidence, committed ledger, queue/lock state, deterministic terminal state |
| SC38–SC44 | representative high-risk table/index/value fixtures rather than the full functional matrix | persistence boundary, recovery, replica, task/client status, cleanup evidence |
| SC45–SC47 | representative semantically proven fixtures across all delivered type families | latency/throughput/resource evidence, stability trends, reproducible defect package |
| SC48 | explicitly out-of-scope INSTANT and switch combinations | scope status and handoff evidence; never count as current PASS |

For every scene, write at least four concrete prerequisites and five concrete observation points. Include environment limits, timeout/stop/cleanup conditions in fault, concurrency, and performance scenes. Do not use generic text such as “check everything is normal.”

- [ ] **Step 5: Run policy tests and confirm they pass**

Run:

```bash
python3 -m unittest -v test_scenario_markdown.ScenarioPolicyTests
```

Expected: all policy tests PASS, with 48 records and nine factor categories per record.

- [ ] **Step 6: Commit the policy layer**

```bash
git add .codex_tmp/online_modify_xmind_20260910_v4_md/scenario_policies.py .codex_tmp/online_modify_xmind_20260910_v4_md/test_scenario_markdown.py
git commit -m "test: define online modify scenario coverage policies"
```

### Task 2: Parse the XMind and normalize the source model

**Files:**

- Create: `.codex_tmp/online_modify_xmind_20260910_v4_md/xmind_model.py`
- Modify: `.codex_tmp/online_modify_xmind_20260910_v4_md/test_scenario_markdown.py`

- [ ] **Step 1: Add failing parser tests**

Add tests for the known immutable source facts:

```python
from pathlib import Path

from xmind_model import load_xmind, source_stats

SOURCE = Path(__file__).parents[2] / "outputs/online_modify_xmind_20260910_v3/RDS_MySQL_8.0.45_测试计划反串讲_V3_逐项通俗说明版.xmind"


class XMindModelTests(unittest.TestCase):
    def test_source_shape(self):
        sheets = load_xmind(SOURCE)
        self.assertEqual(3, len(sheets))
        self.assertEqual(
            [
                "01 测试点（逐项通俗说明）",
                "02 综合场景（由简到繁）",
                "03 附录（原用例与检查点）",
            ],
            [sheet["title"] for sheet in sheets],
        )
        self.assertEqual(7317, source_stats(sheets)["topic_count"])
        self.assertEqual(48, source_stats(sheets)["scene_count"])
```

- [ ] **Step 2: Run tests and confirm the expected import failure**

Run `python3 -m unittest -v test_scenario_markdown.XMindModelTests`.

Expected: FAIL because `xmind_model` does not exist.

- [ ] **Step 3: Implement the read-only parser**

Implement `load_xmind(path)`, `walk_topic(topic)`, `topic_note(topic)`, `scene_id(title)`, `find_scenes(sheets)`, and `source_stats(sheets)`. The parser must read `content.json` from the ZIP without extracting or modifying the source. A normalized scene exposes its title, priority, original seven sections, notes, references, and topic ID.

- [ ] **Step 4: Run parser and policy tests**

Run `python3 -m unittest -v test_scenario_markdown`.

Expected: all tests PASS and report 3 sheets, 7,317 topics, and 48 scenes.

- [ ] **Step 5: Commit the parser**

```bash
git add .codex_tmp/online_modify_xmind_20260910_v4_md/xmind_model.py .codex_tmp/online_modify_xmind_20260910_v4_md/test_scenario_markdown.py
git commit -m "feat: parse online modify xmind source"
```

### Task 3: Render the scenario-first Markdown body

**Files:**

- Create: `.codex_tmp/online_modify_xmind_20260910_v4_md/render_markdown.py`
- Modify: `.codex_tmp/online_modify_xmind_20260910_v4_md/test_scenario_markdown.py`

- [ ] **Step 1: Add failing renderer tests**

Add tests that call `render_document(sheets, policies)` and assert:

```python
class RendererTests(unittest.TestCase):
    def test_every_scene_has_required_sections(self):
        text = self.rendered
        for i in range(1, 49):
            sid = f"SC{i:02d}"
            block = extract_scene_block(text, sid)
            for heading in (
                "场景目标", "前置条件", "覆盖因子", "子运行组合",
                "执行步骤", "观测点", "预期结果与验收", "来源与追溯",
            ):
                self.assertIn(f"#### {heading}", block, (sid, heading))
            self.assertIn("表结构、存储与物理状态", block, sid)
            self.assertIn("索引、约束与对象依赖", block, sid)
            self.assertIn("数据值、规模与分布", block, sid)

    def test_observation_points_are_evidence_based(self):
        for i in range(1, 49):
            block = extract_scene_block(self.rendered, f"SC{i:02d}")
            observations = extract_section(block, "观测点")
            self.assertIn("证据", observations)
            self.assertRegex(observations, r"通过|失败|BLOCKED|范围外")
```

- [ ] **Step 2: Run renderer tests and confirm they fail**

Run `python3 -m unittest -v test_scenario_markdown.RendererTests`.

Expected: FAIL because `render_markdown` does not exist.

- [ ] **Step 3: Implement deterministic rendering**

Implement the renderer as pure functions. The escaping and the two policy-driven tables use this exact behavior:

```python
import re

from scenario_policies import FACTOR_CATEGORIES


def md_text(value):
    return str(value).replace("\\", "\\\\").replace("|", "\\|").strip()


def md_anchor(value):
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")


def render_factor_table(policy):
    lines = [
        "| 因子类别 | 覆盖要求 | 具体范围或例外 | 执行策略 |",
        "|---|---|---|---|",
    ]
    for category in FACTOR_CATEGORIES:
        item = policy["factor_scopes"][category]
        lines.append(
            "| " + " | ".join(
                md_text(value)
                for value in (
                    category,
                    item["requirement"],
                    item["range"],
                    item["strategy"],
                )
            ) + " |"
        )
    return "\n".join(lines)


def render_observations(policy):
    lines = []
    for item in policy["observation_points"]:
        lines.append(
            f'- **{md_text(item["object"])}**：'
            f'证据：{md_text(item["evidence"])}；'
            f'判定：{md_text(item["decision"])}'
        )
    return "\n".join(lines)
```

Implement `render_global_scope(sheets)`, `render_factor_catalog(sheets)`, `render_scene(scene, policy)`, `render_source_appendix(sheets)`, and `render_document(sheets, policies)` around those helpers. Each returns a Markdown string, joins child blocks with exactly one blank line, and preserves source order. `render_document` concatenates the five required document regions in the order stated in the design and terminates the file with one newline.

The document order is: title and generation notice, scope, global prerequisites, 96-dimension factor catalog, 48 enriched scenes in original family order, complete source appendix, and integrity summary. Preserve source notes beneath their topics using blockquotes or indented list content, escape table delimiters, and create stable anchors from existing IDs.

- [ ] **Step 4: Preserve original scene content inside the new structure**

Map original sections without loss:

- `场景条件` feeds scene goal and factor context;
- `执行顺序` remains under execution steps;
- `预期与校验` remains under acceptance;
- `必跑变体` feeds subrun combinations;
- `关联测试维度`, `原始用例来源`, and `原编号技术核对` remain under traceability.

Add policies around these source sections; do not replace or paraphrase away the original assertions.

- [ ] **Step 5: Run the complete unit-test module**

Run `python3 -m unittest -v test_scenario_markdown`.

Expected: all tests PASS; two consecutive `render_document` calls return byte-identical text.

- [ ] **Step 6: Commit the renderer**

```bash
git add .codex_tmp/online_modify_xmind_20260910_v4_md/render_markdown.py .codex_tmp/online_modify_xmind_20260910_v4_md/test_scenario_markdown.py
git commit -m "feat: render scenario-first online modify markdown"
```

### Task 4: Add strict artifact verification

**Files:**

- Create: `.codex_tmp/online_modify_xmind_20260910_v4_md/verify_markdown.py`
- Modify: `.codex_tmp/online_modify_xmind_20260910_v4_md/test_scenario_markdown.py`

- [ ] **Step 1: Add failing verifier tests**

Require the verifier to reject a missing scene section, missing source ID, a blank observation item, an unexplained placeholder, a duplicate SC heading, and a changed source hash. Require it to accept the complete rendered document.

- [ ] **Step 2: Run focused verifier tests and confirm failure**

Run `python3 -m unittest -v test_scenario_markdown.VerifierTests`.

Expected: FAIL because `verify_markdown` does not exist.

- [ ] **Step 3: Implement verification and JSON evidence output**

Implement `verify(source_path, markdown_text)` returning a JSON-serializable report with:

```python
{
    "source_sha256": "8e2b1b212c52eb8c9456b83cba66dfcb8a9e2e85430addb376b270e6e4ced978",
    "source_unchanged": True,
    "sheet_count": 3,
    "topic_count": 7317,
    "scenario_count": 48,
    "scenario_priorities": {"P0": 44, "P1": 3, "P2": 1},
    "dimension_count": 96,
    "original_check_count": 302,
    "original_case_count": 1602,
    "syntax_count": 155,
    "common_factor_count": 35,
    "contract_count": 16,
    "missing_required_sections": [],
    "missing_source_ids": [],
    "unmapped_dimension_ids": [],
    "duplicate_scene_ids": [],
    "broken_internal_links": [],
    "placeholder_hits": [],
    "errors": [],
}
```

The command exits nonzero if `errors` is nonempty and writes `verification.json` only after all checks run. It treats any of the 96 dimensions not attached to at least one scenario as an error and verifies every generated internal anchor target.

- [ ] **Step 4: Run all unit tests**

Run `python3 -m unittest -v test_scenario_markdown`.

Expected: all tests PASS, including deliberate rejection cases.

- [ ] **Step 5: Commit the verifier**

```bash
git add .codex_tmp/online_modify_xmind_20260910_v4_md/verify_markdown.py .codex_tmp/online_modify_xmind_20260910_v4_md/test_scenario_markdown.py
git commit -m "test: verify complete xmind markdown coverage"
```

### Task 5: Generate the final Markdown and verification evidence

**Files:**

- Create: `outputs/online_modify_xmind_20260910_v3/RDS_MySQL_8.0.45_测试计划_V4_场景化完整覆盖版.md`
- Create: `.codex_tmp/online_modify_xmind_20260910_v4_md/verification.json`

- [ ] **Step 1: Record the source XMind hash**

Run:

```bash
shasum -a 256 outputs/online_modify_xmind_20260910_v3/RDS_MySQL_8.0.45_测试计划反串讲_V3_逐项通俗说明版.xmind
```

Expected SHA-256: `8e2b1b212c52eb8c9456b83cba66dfcb8a9e2e85430addb376b270e6e4ced978`.

- [ ] **Step 2: Generate the Markdown deterministically**

Run:

```bash
python3 .codex_tmp/online_modify_xmind_20260910_v4_md/render_markdown.py
```

Expected: the V4 Markdown is created and the command reports 48 rendered scenes and 3 source sheets.

- [ ] **Step 3: Run the strict verifier**

Run:

```bash
python3 .codex_tmp/online_modify_xmind_20260910_v4_md/verify_markdown.py
```

Expected: exit 0; `verification.json` contains `errors: []`, all counts match the source, and `source_unchanged` is true.

- [ ] **Step 4: Run content sanity checks**

Run:

```bash
rg -n '^### SC[0-9]{2} ' outputs/online_modify_xmind_20260910_v3/RDS_MySQL_8.0.45_测试计划_V4_场景化完整覆盖版.md | wc -l
rg -n '^#### (场景目标|前置条件|覆盖因子|子运行组合|执行步骤|观测点|预期结果与验收|来源与追溯)$' outputs/online_modify_xmind_20260910_v3/RDS_MySQL_8.0.45_测试计划_V4_场景化完整覆盖版.md | wc -l
```

Expected: first command prints `48`; second command prints `384`.

- [ ] **Step 5: Review every scene through compact extracts**

Generate a compact review stream containing each scene heading, goal, factor table, and observation points. Read all 48 blocks and correct any scene whose wording is generic, whose scope contradicts its original variants, or whose observation point lacks evidence and a pass/fail rule. Re-run Tasks 1–4 tests after corrections.

- [ ] **Step 6: Verify source immutability and final diff quality**

Run:

```bash
shasum -a 256 outputs/online_modify_xmind_20260910_v3/RDS_MySQL_8.0.45_测试计划反串讲_V3_逐项通俗说明版.xmind
git diff --check -- .codex_tmp/online_modify_xmind_20260910_v4_md outputs/online_modify_xmind_20260910_v3/RDS_MySQL_8.0.45_测试计划_V4_场景化完整覆盖版.md
```

Expected: the XMind hash is unchanged and `git diff --check` emits no errors.

- [ ] **Step 7: Commit the generated artifact and evidence**

```bash
git add .codex_tmp/online_modify_xmind_20260910_v4_md outputs/online_modify_xmind_20260910_v3/RDS_MySQL_8.0.45_测试计划_V4_场景化完整覆盖版.md
git commit -m "docs: add complete online modify scenario markdown"
```

### Task 6: Independent requirement and content review

**Files:**

- Review: `docs/superpowers/specs/2026-09-10-online-modify-xmind-scenario-markdown-design.md`
- Review: `outputs/online_modify_xmind_20260910_v3/RDS_MySQL_8.0.45_测试计划_V4_场景化完整覆盖版.md`
- Review: `.codex_tmp/online_modify_xmind_20260910_v4_md/verification.json`

- [ ] **Step 1: Run an independent spec-compliance review**

Check every design requirement against an exact Markdown section or verifier result. Confirm the document is scenario-first, contains all source material, and uses concise “全部覆盖” labels with explicit exceptions instead of Cartesian expansion.

- [ ] **Step 2: Run an independent domain review**

Review SC01–SC48 for incorrect MySQL assumptions, incompatible combinations, missing high-risk values, unclear observation evidence, and confusion between observation points and injection/synchronization points.

- [ ] **Step 3: Apply review corrections and repeat verification**

For every actionable issue, change the policy or renderer source, regenerate the Markdown, run `python3 -m unittest -v test_scenario_markdown`, and run `python3 verify_markdown.py` until both pass with `errors: []`.

- [ ] **Step 4: Commit review corrections if any**

```bash
git add .codex_tmp/online_modify_xmind_20260910_v4_md outputs/online_modify_xmind_20260910_v3/RDS_MySQL_8.0.45_测试计划_V4_场景化完整覆盖版.md
git commit -m "docs: refine online modify scenario coverage"
```

- [ ] **Step 5: Prepare the delivery summary**

Report the final Markdown path, source XMind hash preservation, scene/section/count verification, test command results, and any `BLOCKED`, contract-pending, or out-of-scope items that remain by design.
