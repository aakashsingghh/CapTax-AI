# CapTax AI — Multi-Broker Capital Gains & Foreign Asset Tax Disclosure Engine

**Team 15** | GLA University, Mathura
Round 2 prototype — B.Tech CSE (AIML), III Year, V Semester (2026–27)

## What this is

A simplified end-to-end pipeline that takes raw trade exports from four
Indian/foreign brokers, normalizes them, matches gains via FIFO, classifies
LTCG/STCG, computes DTAA relief on foreign dividends, and generates a
disclosure summary approximating ITR Schedules CG, FA and FSI. Split into
**backend**, **AI/ML**, and **frontend** layers mapped directly to each
team member's role.

This is a **working scaffold**, not a finished product — every module is
intentionally simple so it's easy to deepen before Round 3.

## 4. Team and Roles

| Member | Role | Responsibilities | Key skills | Availability | Contact |
|---|---|---|---|---|---|
| Shraddha Singh | Team Lead & AI/Interpretation Lead | Scope, tax-rule research, LLM interpretation layer, DTAA logic | Python, LangChain, LLM APIs | 10 hrs/wk | shraddha.singh_cs.aiml24@gla.ac.in |
| Anishka Jain | Backend & Data Lead | Ingestion adapters, reconciliation engine, DB schema | Python, FastAPI, PostgreSQL | 10 hrs/wk | anishka.jain_cs.aiml24@gla.ac.in |
| Akash Singh Chauhan | Frontend & QA Lead | Dashboard UI, disclosure preview, testing, docs | React, Tailwind, Playwright | 8 hrs/wk | akash.chauhan_cs.aiml24@gla.ac.in |

## 5. Week-wise Plan and Assignments

| Week | Milestones | Shraddha (Lead/AI) | Anishka (Backend) | Akash (Frontend/QA) | Deliverables | Status |
|---|---|---|---|---|---|---|
| Week 1 | Requirements freeze | Finalize scope & tax-rule catalog | Broker data-format survey | UI wireframes | Draft SRS, rule catalog v0 | Planned |
| Week 2 | Architecture & DB | Architecture review | Schema & migrations | UI kit | ERD, API spec v1 | Planned |
| Week 3 | Ingestion module | Risk review, unblock | Broker adapters (Zerodha, Groww, Upstox) | Auth screens | Ingestion service v1 | **Done — this codebase** |
| Week 4 | Reconciliation engine | Rule-engine design | Corporate action & FX logic | Dashboard shell | Reconciliation module | **Done — this codebase** |
| Week 5 | AI interpretation layer | LLM integration for LTCG/STCG | Cost-basis (FIFO) matching | Gainsgit 