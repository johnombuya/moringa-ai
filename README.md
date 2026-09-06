# Moringa Applied AI Engineering

Coursework for [Moringa School’s Applied AI Engineering programme](https://moringaschool.com/courses/applied-ai-engineering/). In progress; expected completion October 2026.

This repository is a course monorepo. Each week’s labs and both capstones live in their own folders. API keys stay in local `.env` files (copy from `.env.example` where present) and are never committed.

## Layout

| Folder | Contents |
|---|---|
| [`week1/`](week1/) | Week 1 labs (prompting, embeddings, tokenization) |
| [`capstone-project-week1/`](capstone-project-week1/) | AfyaPlus Triage Engine — LLM classifier with strict JSON routing, cloud + Ollama fallback |
| [`week2/`](week2/) | Week 2 labs (LangChain agents, LlamaIndex RAG, tools, PII masking, MCP) |
| [`capstone-project-week2/`](capstone-project-week2/) | AfyaPlus Enterprise RAG Agent — masking, grounded retrieval, tool calling, session memory |
| [`week3/`](week3/) | Evaluation (BLEU/ROUGE/F1, LLM-as-judge), drift (Evidently), cost labs |
| [`capstone-project-week3/`](capstone-project-week3/) | AfyaPlus observability — evaluation, drift, cost, FastAPI dashboard |
| [`week4/`](week4/) | Fine-tuning data preparation (JSONL / instruction format) |

## Capstones

- **Week 1:** see [`capstone-project-week1/README.md`](capstone-project-week1/README.md). Run from that folder after copying `.env.example` to `.env`.
- **Week 2:** see [`capstone-project-week2/README.md`](capstone-project-week2/README.md). Dedicated GitHub repo and PR: [johnombuya/capstone-project-week2](https://github.com/johnombuya/capstone-project-week2) ([PR #1](https://github.com/johnombuya/capstone-project-week2/pull/1)).
- **Week 3:** see [`capstone-project-week3/README.md`](capstone-project-week3/README.md). Dedicated repo: [johnombuya/capstone-project-week3](https://github.com/johnombuya/capstone-project-week3) ([PR #1](https://github.com/johnombuya/capstone-project-week3/pull/1)).

## Setup

1. Use a Python 3.12+ virtual environment (do not commit `.venv`).
2. For a given project, `cd` into its folder and install `requirements.txt` if present.
3. Copy `.env.example` to `.env` and add your own key. Leave `OPENAI_BASE_URL` unset for direct OpenAI embeddings on the Week 2 capstone.

## Honesty

This is coursework, not a production AfyaPlus deployment. The NVIDIA NCA-GENL exam is programme prep only; this repo does not claim NVIDIA certification.
