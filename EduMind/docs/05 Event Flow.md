# EduMind Architecture Blueprint

Version: v1.0

Document: 05_Event_Flow.md

Status: Architecture Freeze

---

# 1. Purpose

This document defines the runtime workflow of EduMind.

It specifies how requests travel through the system, how modules collaborate, and how responses are generated.

All runtime behavior must follow the event flows defined in this document.

---

# 2. Runtime Principle

EduMind follows a centralized event-driven workflow.

All requests must follow the same execution path.

```text id="p8u1vf"
User

↓

Frontend

↓

FastAPI

↓

Learning Orchestrator

↓

Business Modules

↓

Learning Orchestrator

↓

FastAPI

↓

Frontend

↓

User
```

No business module may bypass the Learning Orchestrator.

---

# 3. Core Events

EduMind V1 defines four core business events.

* Student Login
* Learning Assessment
* AI Learning Conversation
* Learning Completion

Every user interaction belongs to one of these events.

---

# 4. Event 1 - Student Login

## Description

Executed when a student enters the system.

---

## Workflow

```text id="22wwlg"
Student Login

↓

Frontend

↓

FastAPI

↓

Learning Orchestrator

↓

Student Profile

↓

Load Current Learning Status

↓

Return Homepage
```

---

## Module Responsibilities

Learning Orchestrator

* Coordinate login workflow

Student Profile

* Load student information
* Load learning status

---

## Output

* Student information
* Current learning progress
* Current learning plan

---

# 5. Event 2 - Learning Assessment

## Description

Executed after a student finishes an assessment.

---

## Workflow

```text id="3b8snm"
Assessment Submitted

↓

Frontend

↓

FastAPI

↓

Learning Orchestrator

↓

Student Profile

↓

Update Mastery

↓

Recommendation Engine

↓

Generate Learning Plan

↓

Return Assessment Result
```

---

## Module Responsibilities

Student Profile

* Update mastery information

Recommendation Engine

* Generate new learning path

---

## Output

* Updated mastery
* New learning plan
* Recommendation reason

---

# 6. Event 3 - AI Learning Conversation

## Description

Executed when the student asks learning-related questions.

---

## Workflow

```text id="1h2jtm"
Student Question

↓

Frontend

↓

FastAPI

↓

Learning Orchestrator

↓

Student Profile

↓

RAG Module

↓

LLM Service

↓

Learning Orchestrator

↓

Return AI Response
```

---

## Module Responsibilities

Student Profile

* Provide learning context

RAG Module

* Retrieve educational materials

LLM Service

* Generate educational response

---

## Output

* AI answer
* Learning explanation
* Reference resources

---

# 7. Event 4 - Learning Completion

## Description

Executed after a student completes a learning task.

---

## Workflow

```text id="j7q9z0"
Learning Completed

↓

Frontend

↓

FastAPI

↓

Learning Orchestrator

↓

Student Profile

↓

Update Learning Progress

↓

Recommendation Engine

↓

Generate Next Learning Plan

↓

Return Updated Progress
```

---

## Module Responsibilities

Student Profile

* Update learning records
* Update mastery status

Recommendation Engine

* Generate next recommendation

---

## Output

* Updated progress
* Updated learning plan

---

# 8. Standard Execution Flow

Every request must follow the same execution lifecycle.

```text id="87l9gz"
Receive Request

↓

Validate Request

↓

Determine Event Type

↓

Execute Workflow

↓

Collect Results

↓

Generate Response

↓

Return Response
```

---

# 9. Error Flow

If an error occurs during execution:

```text id="jlwmgk"
Request

↓

Learning Orchestrator

↓

Business Module

↓

Error

↓

Standard Error Object

↓

Learning Orchestrator

↓

FastAPI

↓

Frontend
```

Errors must never be returned directly from business modules.

The Learning Orchestrator is responsible for unified error handling.

---

# 10. State Update Rules

Only Student Profile may update learning state.

The following events update Student Profile.

* Assessment completed
* Learning completed
* Student preference updated

The following events do not update Student Profile.

* Resource retrieval
* AI response generation
* Frontend rendering

---

# 11. Data Flow Rules

Business modules receive only the data required for execution.

Example

Recommendation Engine receives:

* Student Profile

It does not receive:

* Chat history
* Raw database objects
* Frontend information

Example

LLM Service receives:

* Prompt
* Student summary
* Retrieved context

It does not receive:

* Database connection
* Recommendation algorithm
* Frontend request

---

# 12. Event Sequence Rules

Every event must satisfy the following order.

```text id="rjc2tu"
Request

↓

Learning Orchestrator

↓

Business Processing

↓

Result Collection

↓

Response Generation

↓

Return
```

Modules may not skip any step.

---

# 13. Event Consistency

Each event must satisfy the following principles.

* Deterministic execution
* Standardized input
* Standardized output
* Independent execution
* No circular invocation

All workflows must remain predictable.

---

# 14. Runtime Summary

EduMind executes all runtime behavior through one centralized workflow.

Learning Orchestrator controls execution.

Business modules execute independent responsibilities.

Student Profile maintains learning state.

This event flow forms the runtime foundation of EduMind.

---

# 15. Next Document

Next:

06_API_Spec.md

This document defines all public REST APIs, request formats, response formats, and interface specifications used by EduMind.
