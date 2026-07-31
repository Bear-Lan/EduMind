# EduMind Architecture Blueprint

Version: v1.0

Document: 00_Project_Overview.md

Status: Draft

---

# 1. Project Overview

## Project Name

**EduMind**

AI Learning Coach Based on Large Language Model and Retrieval-Augmented Generation (RAG)

---

## Project Vision

EduMind is an intelligent learning planning system designed for educational scenarios.

Unlike traditional AI chatbots, EduMind does not simply answer questions. Instead, it continuously analyzes a student's learning state, generates personalized learning paths, provides explainable recommendations, and dynamically adjusts future learning plans based on ongoing learning behavior.

The system is designed around one core objective:

> Help every student learn the right knowledge at the right time.

---

# 2. Project Objectives

The MVP (Minimum Viable Product) focuses on building a complete learning loop instead of implementing numerous isolated features.

The first version must support the following workflow:

Student Login

↓

Knowledge Assessment

↓

Student Profile Generation

↓

Learning Path Recommendation

↓

AI Learning Assistance

↓

Learning Progress Update

↓

Learning Path Adjustment

This workflow represents the complete product capability of EduMind V1.

---

# 3. Project Positioning

EduMind is **NOT** designed as:

* A chatbot
* A search engine
* An AI homework solver
* A knowledge base

EduMind **IS** designed as:

> An AI Learning Coach.

Its primary responsibility is to assist students in planning and managing their learning process rather than simply answering questions.

---

# 4. MVP Scope

The first version intentionally limits the system scope.

Included:

* Student profile management
* Learning path recommendation
* RAG-based educational knowledge retrieval
* AI explanation and tutoring
* Learning progress recording
* Basic visualization

Excluded:

* Knowledge Graph
* Multi-Agent Architecture
* MCP Integration
* Voice Interaction
* Reinforcement Learning
* Multi-modal Input
* Adaptive Testing (IRT)
* Complex Recommendation Algorithms

These features may be considered in future versions but are outside the scope of EduMind V1.

---

# 5. Core Design Philosophy

The system follows four design principles.

## Principle 1

Single Responsibility

Every module has only one responsibility.

Example:

Recommendation Engine decides **what to learn**.

LLM decides **how to explain**.

Neither should perform the other's responsibility.

---

## Principle 2

Single Source of Truth

Student Profile is the only source of student state.

All learning status, progress, and recommendations must be based on Student Profile.

No other module should maintain independent student status.

---

## Principle 3

Separation of Decision and Generation

Decision making and language generation are separated.

Recommendation Engine:

* Generates learning priorities.

LLM:

* Explains recommendations.
* Generates natural language.
* Assists student interaction.

The LLM should never independently determine learning priorities.

---

## Principle 4

Modular Architecture

Every core module should be independently replaceable.

For example:

* Qwen can be replaced by another LLM.
* Qdrant can be replaced by another vector database.
* Recommendation algorithms can be upgraded without affecting other modules.

Module independence is mandatory.

---

# 6. Core Workflow

The entire system revolves around one continuous learning cycle.

Student Action

↓

Student Profile Update

↓

Learning Recommendation

↓

Knowledge Retrieval

↓

LLM Response

↓

Learning Completion

↓

Student Profile Update

↓

Repeat

This loop forms the core operational logic of EduMind.

---

# 7. Technical Strategy

The project adopts mature and stable technologies rather than experimental architectures.

Recommended technology stack:

Backend

* FastAPI

Frontend

* Vue 3 (or React)

Database

* PostgreSQL

Vector Database

* Qdrant

Large Language Model

* Qwen or DeepSeek

Knowledge Enhancement

* Retrieval-Augmented Generation (RAG)

This technology selection prioritizes engineering stability, rapid development, and demonstration reliability.

---

# 8. Development Principles

During development, every implementation must comply with the following rules.

* Build architecture before implementing features.
* Keep modules loosely coupled.
* Avoid premature optimization.
* Ensure every module can be independently tested.
* Every new feature must fit into the existing architecture instead of modifying it.

---

# 9. Success Criteria

EduMind V1 is considered complete when the following conditions are satisfied.

The system can:

* Complete a full learning workflow.
* Generate personalized learning paths.
* Answer learning questions using RAG.
* Update student profiles after learning.
* Recommend the next learning objective.
* Demonstrate the complete workflow in a live environment.

No additional advanced features are required for the MVP.

---

# 10. Next Document

The next document is:

01_Architecture.md

It defines the complete software architecture, module boundaries, and system skeleton.

This document serves as the foundation for all subsequent engineering design.
