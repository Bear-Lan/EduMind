# EduMind Architecture Blueprint

Version: v1.0

Document: 01_Architecture.md

Status: Draft

---

# 1. Architecture Overview

EduMind adopts a layered, modular architecture.

The system is designed to achieve:

* High cohesion
* Low coupling
* Independent module development
* Easy future expansion

Each module has a single responsibility and communicates only through the central orchestration layer.

---

# 2. Overall Architecture

```
                 Student
                    │
                    ▼
              Presentation Layer
            (Vue / React Frontend)
                    │
                    ▼
            Application Layer
                  FastAPI
                    │
                    ▼
         Learning Orchestrator
        (Central Decision Engine)
                    │
      ┌─────────────┼─────────────┐
      │             │             │
      ▼             ▼             ▼
Student Profile  Recommendation   RAG
                                      │
                                      ▼
                                   LLM Service
                    │
                    ▼
               Data Layer
(PostgreSQL + Vector Database)
```

The Learning Orchestrator is the only component responsible for coordinating system behavior.

---

# 3. Layer Definition

## Presentation Layer

Purpose

Provide user interaction.

Responsibilities

* Login
* Assessment interface
* Chat interface
* Learning plan visualization
* Learning report visualization

Rules

* No business logic.
* No database access.
* No AI processing.

---

## Application Layer

Component

FastAPI

Purpose

Receive external requests and dispatch them to the Core Layer.

Responsibilities

* API Routing
* Authentication
* Request validation
* Response formatting
* Exception handling

Rules

* Must not contain business logic.
* Must not calculate recommendation results.
* Must not directly access AI models.

---

## Core Layer

The Core Layer contains the business capabilities of EduMind.

It consists of four independent modules.

---

### Student Profile Module

Purpose

Maintain the student's current learning state.

Responsibilities

* Create profile
* Read profile
* Update profile
* Maintain mastery status
* Maintain learning history

Output

Current student state.

---

### Recommendation Engine

Purpose

Determine what the student should learn next.

Responsibilities

* Calculate learning priority
* Generate learning path
* Produce recommendation result

Rules

* Must not generate natural language.
* Must not call the LLM directly.

Output

Structured recommendation data.

---

### RAG Module

Purpose

Provide reliable educational knowledge.

Responsibilities

* Retrieve relevant documents
* Perform vector search
* Return educational context

Rules

* Never generate answers.
* Only retrieve knowledge.

Output

Retrieved learning materials.

---

### LLM Service

Purpose

Generate human-readable responses.

Responsibilities

* Answer questions
* Explain recommendations
* Generate study plans
* Summarize learning progress

Rules

* Never retrieve documents directly.
* Never decide learning priorities.
* Only process provided context.

---

# 4. Data Layer

The Data Layer stores all persistent information.

Components

PostgreSQL

Stores

* Student
* Learning History
* Learning Plan
* Session
* Resource Metadata

Vector Database

Stores

* Text Embeddings
* Educational Resources
* Curriculum Documents

Rules

Business modules never communicate with databases directly unless explicitly defined.

---

# 5. Learning Orchestrator

Learning Orchestrator is the central controller of EduMind.

Purpose

Coordinate all business modules.

Responsibilities

* Determine workflow
* Invoke business modules
* Transfer intermediate results
* Control execution order

Learning Orchestrator is the only module allowed to coordinate multiple services.

No other module may directly invoke another business module.

---

# 6. Dependency Rules

The dependency direction must always remain:

Presentation

↓

Application

↓

Learning Orchestrator

↓

Business Modules

↓

Data Layer

Reverse dependencies are prohibited.

Business modules must remain independent.

---

# 7. Module Communication Rules

Allowed

FastAPI

↓

Learning Orchestrator

↓

Student Profile

Learning Orchestrator

↓

Recommendation

Learning Orchestrator

↓

RAG

Learning Orchestrator

↓

LLM

Prohibited

Recommendation

→

LLM

RAG

→

Recommendation

LLM

→

Database

Presentation

→

Database

Business modules must never communicate directly unless explicitly coordinated by Learning Orchestrator.

---

# 8. Architectural Principles

EduMind follows the following engineering principles.

Single Responsibility Principle

Every module has exactly one responsibility.

Loose Coupling

Modules should know as little as possible about each other.

Replaceability

Every module can be replaced independently.

Centralized Decision

All workflow decisions belong to Learning Orchestrator.

State Consistency

Student Profile is the only source of student state.

---

# 9. Architecture Stability

The architecture defined in this document is considered stable.

Future versions may replace implementations but should not change module responsibilities.

All future features must be integrated into the existing architecture rather than modifying module boundaries.

---

# 10. Next Document

Next:

02_Directory_Structure.md

This document defines the engineering directory structure and project organization rules.
