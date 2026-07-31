# EduMind Architecture Blueprint

Version: v1.0

Document: 99_Engineering_Rules.md

Status: Architecture Freeze

Priority: Highest

---

# 1. Purpose

This document defines the mandatory engineering rules for the EduMind project.

Every contributor, including human developers and AI coding assistants (such as Roo Code, Cursor, Claude, and ChatGPT), must follow these rules.

These rules take precedence over implementation preferences.

---

# 2. Architecture Freeze

The system architecture is frozen.

The following documents are the Single Source of Truth (SSOT):

* 00_Project_Overview.md
* 01_Architecture.md
* 02_Directory_Structure.md
* 03_Data_Model.md
* 04_Module_Design.md
* 05_Event_Flow.md
* 06_API_Spec.md
* 07_Development_Roadmap.md
* 99_Engineering_Rules.md

No contributor may modify the architecture without explicit approval.

---

# 3. Single Responsibility Principle

Every module must have exactly one responsibility.

Examples

Student Profile

Responsible for:

* Student learning state

Not responsible for:

* AI generation
* Recommendation
* Resource retrieval

Recommendation Engine

Responsible for:

* Learning path generation

Not responsible for:

* Database management
* Chat
* LLM interaction

---

# 4. Learning Orchestrator Rule

The Learning Orchestrator is the only coordinator of business modules.

Allowed

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

Forbidden

```text
Recommendation → RAG

LLM → Recommendation

Student Profile → LLM

RAG → Student Profile
```

Business modules must never call each other directly.

---

# 5. Module Independence

Every module must be independently:

* Developed
* Tested
* Replaced
* Maintained

No module should depend on the internal implementation of another module.

Communication must occur only through public interfaces.

---

# 6. API Rules

The API layer is responsible only for:

* Receiving requests
* Validating requests
* Returning responses

The API layer must never:

* Execute business logic
* Query the database directly
* Invoke multiple business modules independently

Every request must be forwarded to the Learning Orchestrator.

---

# 7. Database Rules

Business modules must never manipulate database connections directly.

Database access must be encapsulated.

Persistent data and temporary runtime data must remain separated.

Database schemas must follow the definitions in 03_Data_Model.md.

---

# 8. Student State Rule

Student Profile is the Single Source of Truth (SSOT).

Only Student Profile may modify:

* Learning progress
* Mastery information
* Learning preferences
* Current learning state

Other modules may read the data but must never modify it directly.

---

# 9. LLM Rules

The LLM Service is responsible only for language generation.

The LLM must never:

* Decide learning priorities
* Retrieve documents directly
* Modify student data
* Execute recommendation algorithms

Its input must always come from the Learning Orchestrator.

---

# 10. RAG Rules

The RAG Module is responsible only for knowledge retrieval.

The RAG Module must never:

* Generate responses
* Recommend learning paths
* Update databases
* Modify student information

Its responsibility ends after returning retrieved context.

---

# 11. Recommendation Rules

The Recommendation Engine is responsible only for deciding what the student should learn next.

It must never:

* Generate natural language
* Retrieve learning resources
* Modify Student Profile
* Interact with the frontend

The Recommendation Engine outputs structured recommendation results only.

---

# 12. Coding Standards

General Rules

* Use clear naming.
* Avoid duplicate code.
* Keep functions focused.
* Keep modules small.
* Write readable code before optimizing.

Recommended Limits

* Function: ≤ 50 lines
* Class: ≤ 500 lines
* File: ≤ 800 lines

Large modules should be split into smaller components.

---

# 13. Error Handling

Every module must return standardized error objects.

Modules must never terminate the application.

Only the Learning Orchestrator decides how errors are handled.

All exceptions must be logged.

---

# 14. Logging Rules

The system must log:

* API requests
* Module execution
* Errors
* Warnings
* System startup
* System shutdown

Sensitive information must never appear in logs.

---

# 15. Testing Rules

Every new feature must include appropriate tests.

Minimum requirements:

* Unit Test
* Integration Test
* API Test (where applicable)

New code should not reduce existing system stability.

---

# 16. Security Rules

Never hardcode:

* API Keys
* Database passwords
* Tokens
* Secrets

Use environment variables for all sensitive configuration.

Validate all external input.

---

# 17. Documentation Rules

Every new module must include:

* Purpose
* Responsibilities
* Public Interfaces
* Input
* Output

Every public API must be documented.

Architecture documents must remain synchronized with implementation.

---

# 18. Future Expansion Rules

Future features must extend the architecture rather than modify it.

Examples:

New modules may be added:

* Essay Evaluation
* Learning Report
* Teacher Dashboard
* Knowledge Graph

Existing module responsibilities must not change.

---

# 19. AI Development Rules

When AI coding assistants participate in development:

They must:

* Read all Blueprint documents before coding.
* Follow Architecture Freeze.
* Respect module boundaries.
* Generate code that matches the defined directory structure.
* Avoid introducing hidden dependencies.

If a conflict between implementation and architecture is found:

* Stop implementation.
* Report the conflict.
* Wait for human confirmation.

AI assistants must not redesign the architecture independently.

---

# 20. Definition of Done (DoD)

A development task is considered complete only if:

* Code is implemented.
* Tests pass.
* Documentation is updated.
* No architecture rules are violated.
* Module responsibilities remain unchanged.
* No critical bugs are introduced.

---

# 21. Final Engineering Principle

EduMind follows one fundamental principle:

```text
Architecture First

↓

Module Responsibility

↓

Implementation

↓

Testing

↓

Optimization
```

Never reverse this order.

A stable architecture produces a stable system.

---

# 22. Blueprint Completion

The EduMind Blueprint consists of the following documents:

* 00_Project_Overview.md
* 01_Architecture.md
* 02_Directory_Structure.md
* 03_Data_Model.md
* 04_Module_Design.md
* 05_Event_Flow.md
* 06_API_Spec.md
* 07_Development_Roadmap.md
* 99_Engineering_Rules.md

Together, these documents form the official engineering specification for EduMind V1.

All development work must use this Blueprint as the single source of truth.

End of Blueprint.
