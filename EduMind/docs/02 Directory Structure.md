# EduMind Architecture Blueprint

Version: v1.0

Document: 02_Directory_Structure.md

Status: Architecture Freeze

---

# 1. Purpose

This document defines the engineering directory structure of EduMind.

The purpose of this document is to ensure:

* Consistent project organization
* Clear module boundaries
* Easy maintenance
* Independent module development

The directory structure defined here is considered stable for EduMind V1.

---

# 2. Project Structure

```text
EduMind/
│
├── frontend/
│
├── backend/
│
├── docs/
│
├── scripts/
│
├── tests/
│
├── requirements.txt
│
├── .env.example
│
├── .gitignore
│
└── README.md
```

---

# 3. Root Directory Description

## frontend/

Contains all user interface code.

Responsibilities

* Web UI
* Components
* Pages
* Static Assets
* Frontend Routing

Recommended Framework

Vue 3

---

## backend/

Contains all backend business logic.

This is the core of EduMind.

---

## docs/

Contains all architecture documents.

Examples

* Architecture Blueprint
* API Specification
* Development Roadmap

No source code should be placed here.

---

## scripts/

Contains helper scripts.

Examples

* Initialize database
* Import educational resources
* Generate embeddings
* Build vector database

Scripts should not contain business logic.

---

## tests/

Contains all automated tests.

Recommended structure

```text
tests/

unit/

integration/

api/
```

---

# 4. Backend Structure

```text
backend/

├── main.py

├── api/

├── application/

├── core/

├── services/

├── models/

├── database/

├── recommendation/

├── rag/

├── llm/

├── schemas/

├── config/

└── utils/
```

---

# 5. Backend Directory Responsibilities

## main.py

Application entry point.

Responsibilities

* Start FastAPI
* Register routers
* Load configuration

No business logic allowed.

---

## api/

Contains REST API definitions.

Responsibilities

* HTTP Routes
* Request validation
* Response formatting

Must never implement business logic.

---

## application/

Contains application-level orchestration.

Main component

Learning Orchestrator

Responsibilities

* Coordinate workflow
* Dispatch business modules
* Manage execution order

This directory is the control center of EduMind.

---

## core/

Contains shared system capabilities.

Examples

* Dependency Injection
* Authentication
* Logging
* Error Handling

Business logic should not be placed here.

---

## services/

Contains reusable infrastructure services.

Examples

* File Service
* Embedding Service
* Resource Loader

Services provide technical capabilities but do not make business decisions.

---

## models/

Contains database models.

Examples

Student

LearningHistory

LearningPlan

Session

Resource

Models define persistent storage only.

---

## database/

Contains database initialization.

Responsibilities

* Database connection
* Session management
* Migration support

No business logic allowed.

---

## recommendation/

Contains the Recommendation Engine.

Responsibilities

* Learning priority calculation
* Learning path generation
* Recommendation reasoning

Only structured recommendation results are produced.

---

## rag/

Contains Retrieval-Augmented Generation.

Responsibilities

* Vector retrieval
* Document search
* Context construction

Never generate responses.

---

## llm/

Contains all Large Language Model interaction.

Responsibilities

* Prompt construction
* Response generation
* Explanation generation

Never retrieve knowledge independently.

---

## schemas/

Contains request and response schemas.

Responsibilities

* API Request Models
* API Response Models
* Validation Models

No business logic.

---

## config/

Contains project configuration.

Examples

Database configuration

Model configuration

Environment configuration

API Keys

Configuration must not be hardcoded.

---

## utils/

Contains utility functions.

Examples

Date utilities

Text processing

Common helper functions

Utility functions must remain stateless.

---

# 6. Dependency Rules

Allowed

Frontend

↓

API

↓

Application

↓

Business Modules

↓

Database

Business modules should never depend on frontend components.

Infrastructure should never depend on business modules.

---

# 7. Naming Convention

Directories

snake_case

Example

student_profile

recommendation_engine

Python Files

snake_case

Classes

PascalCase

Functions

snake_case

Constants

UPPER_CASE

Variables

snake_case

Naming consistency is mandatory.

---

# 8. Engineering Rules

Every directory must have a single responsibility.

Business logic must never appear in:

* api/
* config/
* database/
* schemas/
* utils/

Business logic belongs only to business modules.

---

# 9. Future Expansion

Future features should be added without changing the existing directory hierarchy.

Example

Future Feature

Essay Evaluation

New Directory

backend/essay/

Future Feature

Learning Report

New Directory

backend/report/

The architecture should grow by extension rather than modification.

---

# 10. Next Document

Next:

03_Data_Model.md

This document defines all core entities, data structures, relationships, and persistence models used by EduMind.
