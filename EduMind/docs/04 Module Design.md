# EduMind Architecture Blueprint

Version: v1.0

Document: 04_Module_Design.md

Status: Architecture Freeze

---

# 1. Purpose

This document defines the responsibilities, boundaries, inputs, outputs, and public interfaces of every core module in EduMind.

Every module must have:

* A single responsibility
* Clear input and output
* Independent implementation
* Loose coupling
* High cohesion

Modules communicate only through the Learning Orchestrator.

---

# 2. Core Modules

EduMind consists of five core modules.

```text
Learning Orchestrator

├── Student Profile
├── Recommendation Engine
├── RAG Module
└── LLM Service
```

---

# 3. Learning Orchestrator

## Purpose

Acts as the central coordinator of the entire system.

---

## Responsibilities

* Receive business requests
* Determine execution workflow
* Coordinate all business modules
* Collect execution results
* Return final responses

---

## Input

* API requests
* User actions
* Internal events

---

## Output

* Structured execution results
* Final response objects

---

## Public Interfaces

* handle_chat()
* handle_learning_plan()
* handle_assessment()
* handle_learning_completion()

---

## Restrictions

Must not:

* Store student data
* Execute recommendation algorithms
* Retrieve documents
* Generate AI responses

It is responsible only for orchestration.

---

# 4. Student Profile Module

## Purpose

Maintain the current learning state of every student.

---

## Responsibilities

* Create student profile
* Read profile
* Update profile
* Maintain learning status
* Maintain mastery information
* Record learning progress

---

## Input

* Assessment results
* Learning completion events
* Learning behavior
* User preferences

---

## Output

* Student profile
* Learning status
* Mastery information

---

## Public Interfaces

* create_profile()
* get_profile()
* update_profile()
* update_mastery()
* update_learning_progress()

---

## Restrictions

Must not:

* Recommend learning paths
* Retrieve knowledge
* Generate AI responses

---

# 5. Recommendation Engine

## Purpose

Generate personalized learning paths.

---

## Responsibilities

* Calculate learning priority
* Generate learning sequence
* Produce recommendation results
* Explain recommendation reasons

---

## Input

* Student Profile

---

## Output

* Learning Plan
* Recommendation Result

---

## Public Interfaces

* calculate_priority()
* generate_learning_plan()
* explain_recommendation()

---

## Restrictions

Must not:

* Access LLM
* Retrieve documents
* Modify Student Profile
* Access frontend

---

# 6. RAG Module

## Purpose

Retrieve reliable educational knowledge.

---

## Responsibilities

* Vector retrieval
* Document search
* Context construction
* Resource ranking

---

## Input

* User question
* Recommendation topic

---

## Output

* Retrieved context
* Reference documents

---

## Public Interfaces

* retrieve()
* search()
* rerank()
* build_context()

---

## Restrictions

Must not:

* Generate responses
* Update student information
* Produce recommendations

---

# 7. LLM Service

## Purpose

Generate natural language output.

---

## Responsibilities

* Answer questions
* Explain learning concepts
* Explain recommendations
* Generate study guidance
* Summarize conversations

---

## Input

* Prompt
* Retrieved Context
* Student Profile Summary

---

## Output

* AI Response
* Learning Explanation
* Study Suggestion

---

## Public Interfaces

* chat()
* explain()
* summarize()
* generate_response()

---

## Restrictions

Must not:

* Retrieve documents
* Calculate recommendations
* Modify databases directly

---

# 8. Module Dependency

Allowed dependencies

```text
Learning Orchestrator

↓

Student Profile

↓

Recommendation Engine

↓

RAG Module

↓

LLM Service
```

The Learning Orchestrator may invoke any module.

Business modules must never invoke each other directly.

---

# 9. Module Collaboration

## Chat Workflow

Learning Orchestrator

↓

Student Profile

↓

RAG

↓

LLM

↓

Response

---

## Recommendation Workflow

Learning Orchestrator

↓

Student Profile

↓

Recommendation Engine

↓

Learning Plan

---

## Learning Completion Workflow

Learning Orchestrator

↓

Student Profile

↓

Recommendation Engine

↓

Updated Learning Plan

---

## Assessment Workflow

Learning Orchestrator

↓

Student Profile

↓

Recommendation Engine

↓

Assessment Result

---

# 10. Error Handling

Each module is responsible only for its own errors.

Modules must return standardized error objects.

Modules must never terminate the workflow directly.

The Learning Orchestrator determines whether execution should continue.

---

# 11. Design Principles

Every module must satisfy the following principles.

* Single Responsibility
* Independent Testing
* Stateless Execution (except Student Profile persistence)
* Replaceable Implementation
* Standardized Interface

---

# 12. Future Extension

New modules should follow the same structure.

Example

```text
Essay Evaluation Module

Purpose

Responsibilities

Input

Output

Public Interfaces

Restrictions
```

No existing module responsibilities should be modified.

---

# 13. Summary

The module architecture follows one principle:

The Learning Orchestrator coordinates.

Business modules execute.

No module makes decisions outside its defined responsibility.

This separation ensures maintainability, scalability, and clear engineering boundaries.

---

# 14. Next Document

Next:

05_Event_Flow.md

This document defines the complete runtime workflow, event sequence, and interaction process of EduMind.
