# OS/ONS MCP Server Evaluation

This document describes the evaluation framework for assessing the effectiveness of the OS/ONS MCP server in answering user queries.

## Overview

The evaluation framework consists of:
1. **Question Suite** - 30+ diverse test questions
2. **Scoring Rubric** - 5 dimensions, 100 points total
3. **Test Harness** - Automated test execution
4. **Audit Logging** - LLM-readable traces

## Current Evaluation Score

| Metric | Value |
|--------|-------|
| **Overall Score** | 83.75% (16/16) |
| **Level** | Good |
| **Date** | 2026-01-19 |
| **Questions Tested** | 16 (Basic only, including edge/ambiguous) |

### Score by Difficulty

| Difficulty | Score | Status |
|------------|-------|--------|
| Basic | 83.75% (16/16) | ✅ Good |
| Intermediate | _Not tested_ | - |
| Advanced | _Not tested_ | - |

### Score by Intent

| Intent | Score | Status |
|--------|-------|--------|
| place_lookup | 83.18% (11/11) | ✅ |
| dataset_discovery | 91.67% (3/3) | ✅ |
| interactive_selection | 75.00% (2/2) | ✅ |
| statistics | _Not tested_ | - |
| area_comparison | _Not tested_ | - |
| feature_search | _Not tested_ | - |
| boundary_fetch | _Not tested_ | - |
| route_planning | _Not tested_ | - |

---

## Scoring Rubric

### Dimensions

#### 1. Intent Recognition (0-25 points)
Measures how accurately the system identifies what the user wants.

| Score | Criteria |
|-------|----------|
| 25 | Correct intent with high confidence (>0.8) |
| 20 | Correct intent with medium confidence (0.5-0.8) |
| 15 | Correct intent with low confidence (<0.5) |
| 10 | Related but incorrect intent |
| 0 | Completely wrong intent |

#### 2. Tool Selection (0-25 points)
Measures whether the right tools were used.

| Score | Criteria |
|-------|----------|
| 25 | All required tools used, no forbidden tools |
| 20 | All required tools, 1 minor forbidden tool |
| 15 | Most required tools (>50%) |
| 10 | Some required tools |
| 0 | No required tools or multiple forbidden tools |

#### 3. Efficiency (0-20 points)
Measures whether the task was completed without unnecessary steps.

| Score | Criteria |
|-------|----------|
| 20 | At or below expected tool calls |
| 15 | 1-2 extra calls |
| 10 | 3-5 extra calls |
| 5 | 6-10 extra calls |
| 0 | More than 10 extra calls |

#### 4. Response Quality (0-20 points)
Measures the accuracy and completeness of the response.

| Score | Criteria |
|-------|----------|
| 20 | All required keywords, expected values, no forbidden |
| 15 | Most required keywords (>75%) |
| 10 | Some required keywords (>50%) |
| 5 | Few required keywords |
| 0 | Forbidden keywords or no relevant content |

#### 5. Error Handling (0-10 points)
Measures how gracefully errors are handled.

| Score | Criteria |
|-------|----------|
| 10 | No errors OR graceful handling with helpful message |
| 7 | Error occurred but handled gracefully |
| 5 | Error occurred, partially handled |
| 0 | Unhandled error or crash |

### Overall Score Levels

| Level | Percentage | Description |
|-------|-----------|-------------|
| **Excellent** | 90-100% | Outstanding performance |
| **Good** | 75-89% | Solid performance with minor issues |
| **Acceptable** | 60-74% | Meets minimum requirements |
| **Poor** | 40-59% | Below expectations, needs improvement |
| **Fail** | 0-39% | Unacceptable performance |

---

## Question Suite

### Basic Questions (9 questions)
Simple, single-tool queries testing core functionality.

| ID | Question | Expected Intent | Expected Tool |
|----|----------|-----------------|---------------|
| B001 | Find Birmingham | place_lookup | search_geographic_areas |
| B002 | Where is Manchester? | place_lookup | search_geographic_areas |
| B003 | What is the area code for Coventry? | place_lookup | search_geographic_areas |
| B004 | Find Leeds local authority | place_lookup | search_geographic_areas |
| B005 | Search for Edinburgh | place_lookup | search_geographic_areas |
| B006 | What datasets are available? | dataset_discovery | list_ons_datasets |
| B007 | Show me wellbeing datasets | dataset_discovery | list_ons_datasets |
| B008 | Open a map so I can select some areas | interactive_selection | select_geographic_area |
| B009 | Let me pick local authorities on a map | interactive_selection | select_geographic_area |

### Intermediate Questions (12 questions)
Multi-step queries requiring context or multiple tools.

| ID | Question | Expected Intent | Workflow |
|----|----------|-----------------|----------|
| I001 | What is the wellbeing score for Birmingham? | statistics | search → get_statistics |
| I002 | Show me population data for Coventry | statistics | search → get_statistics |
| I003 | What are the house prices in Manchester? | statistics | search → get_statistics |
| I004 | Compare wellbeing between Birmingham and Manchester | area_comparison | search → compare_areas |
| I005 | Which is better, Leeds or Sheffield? | area_comparison | search → compare_areas |
| I006 | Get the boundary of Birmingham | boundary_fetch | search → fetch_boundaries |
| I007 | Show me the shape of Coventry council area | boundary_fetch | search → fetch_boundaries |
| I008 | Find cinemas in Leeds | feature_search | OS NGD workflow |
| I009 | Show buildings near Birmingham city centre | feature_search | OS NGD workflow |
| I010 | Find all schools in Manchester | feature_search | OS NGD workflow |
| I011 | Plan a route from Birmingham to Manchester | route_planning | plan_route |
| I012 | How do I get from Coventry to London? | route_planning | plan_route |

### Advanced Questions (5 questions)
Complex multi-step workflows.

### Edge Cases (5 questions)
Error handling and security tests.

### Ambiguous Questions (3 questions)
Tests intent classification with minimal input.

---

## Running Evaluations

### Quick Test (Basic Questions Only)

```bash
python -m tests.evaluation.harness --difficulty=basic --verbose
```

### Full Evaluation

```bash
python -m tests.evaluation.harness --output=results.json
```

### Specific Intent

```bash
python -m tests.evaluation.harness --intent=place_lookup
```

### Specific Questions

```bash
python -m tests.evaluation.harness --questions=B001,B002,I001
```

---

## Audit Logs

Each query produces an LLM-readable audit log with these sections:

1. **QUERY** - The incoming user question
2. **ROUTING** - Intent classification and tool recommendation
3. **TOOL_CALLS** - Each tool call with inputs and outputs
4. **RESPONSE** - Final response to the user
5. **METRICS** - Performance and efficiency metrics

### Example Audit Log

```
============================================================
AUDIT LOG: a1b2c3d4
Timestamp: 2024-01-18T10:30:00
============================================================

## 1. QUERY
------------------------------------------------------------
User Question: "Find Birmingham"

## 2. ROUTING DECISION
------------------------------------------------------------
Intent Detected: place_lookup
Confidence: 0.95
Recommended Tool: search_geographic_areas
Workflow Steps: search_geographic_areas

## 3. TOOL CALLS
------------------------------------------------------------
### Tool Call 1: route_query
········································
Timestamp: 2024-01-18T10:30:00.100
Duration: 15.3ms
Status: SUCCESS

**Inputs:**
```json
{"query": "Find Birmingham"}
```

**Outputs:**
```json
{
  "intent": "place_lookup",
  "confidence": 0.95,
  "recommended_tool": "search_geographic_areas"
}
```

### Tool Call 2: search_geographic_areas
········································
Timestamp: 2024-01-18T10:30:00.200
Duration: 245.7ms
Status: SUCCESS

**Inputs:**
```json
{"query": "Birmingham", "level": "local_auth"}
```

**Outputs:**
```json
{
  "code": "E08000025",
  "name": "Birmingham",
  "level": "local_auth"
}
```

## 4. FINAL RESPONSE
------------------------------------------------------------
Birmingham is a metropolitan borough with GSS code E08000025.

## 5. METRICS
------------------------------------------------------------
Total Duration: 261.0ms
Tool Calls: 2
Overall Status: SUCCESS

**Tool Call Summary:**
  - route_query: 1x
  - search_geographic_areas: 1x

============================================================
END OF AUDIT LOG
============================================================


---

## Evaluation History

| Date | Version | Score | Notes |
|------|---------|-------|-------|
| 2026-01-19 | v0.1.18 | 83.75% | Basic-only run (includes edge/ambiguous) |
| 2026-01-18 | v0.1.18 | 100% | Sprint 8 - Query Router implementation |

---

## Known Issues

1. **Advanced Questions** - Not yet tested; may need additional patterns
2. **Edge Cases** - Need evaluation for error handling and security tests

---

## Improvement Targets

| Metric | Current | Target | Priority |
|--------|---------|--------|----------|
| Basic Questions | 100% | 95% | ✅ Achieved |
| Intermediate Questions | 100% | 85% | ✅ Achieved |
| Advanced Questions | _TBD_ | 75% | Medium |
| Edge Cases | _TBD_ | 90% | High |

---

## References

- [SKILL.md](../SKILL.md) - Tool usage documentation
- [Tutorial](tutorial.md) - User guide
- [Query Router](../src/tools/query_router.py) - Intent classification
