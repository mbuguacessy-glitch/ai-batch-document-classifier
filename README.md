# AI Batch Document Classifier

## What this does
Automatically scans a folder of documents, classifies each one using Claude AI, and produces a master JSON report showing every document's category, urgency, required action, and whether a deadline was mentioned. Urgent documents are surfaced first.

## The problem it solves
Manually reading 30+ documents to triage them takes hours. This script classifies an entire folder in under 60 seconds, surfacing urgent items immediately so nothing critical is missed.

## Measurable result
- Documents classified during testing: 5
- Processing time: under 60 seconds
- Urgent documents correctly identified: 1/1 (100%)
- Output: master JSON sorted by urgency

## Tech stack — 2026 versions
- Python 3.12.0
- Anthropic SDK 0.40.0
- Claude claude-sonnet-4-5

## How it works
1. scan_documents() finds all .txt files in the documents/ folder
2. read_document() reads the full content of each file
3. classify_document() sends content to Claude with a strict JSON prompt requesting: category, urgency, summary, key_action, deadline_mentioned, estimated_value_kes
4. json.loads() converts Claude's response into a Python dictionary
5. save_results() sorts by urgency, writes master JSON, prints summary

## Document categories supported
contract | complaint | invoice | policy | meeting_notes | other

## Urgency levels
urgent | standard | low

## Error handling
- Missing or empty documents folder caught before any API calls
- Claude returning markdown-wrapped JSON cleaned automatically
- Individual document failures logged — script continues to next file
- API errors caught per document with clear error messages

## Screenshots
[[terminal output ](https://imgur.com/a/EJnAYZQ)]
[[output JSON file ](https://imgur.com/a/UkToYDT)]