# EduMind Architecture Blueprint

Version: v1.0

Document: 06_API_Spec.md

Status: Architecture Freeze

---

# 1. Purpose

This document defines the public API specification of EduMind.

The API layer is responsible only for communication between the frontend and backend.

Business logic must never be implemented inside API endpoints.

All requests must be forwarded to the Learning Orchestrator.

---

# 2. API Design Principles

The API layer follows these principles.

* RESTful design
* JSON request and response
* Unified response format
* Stateless communication
* Standard HTTP status codes

---

# 3. Base URL

```text id="9qrm5e"
/api/v1
```

All APIs must be versioned.

---

# 4. Standard Response Format

## Success Response

```json
{
    "success": true,
    "code": 200,
    "message": "success",
    "data": {}
}
```

---

## Error Response

```json
{
    "success": false,
    "code": 400,
    "message": "error message",
    "data": null
}
```

---

# 5. Authentication APIs

## Login

Method

POST

Endpoint

```text id="wdd4qx"
/api/v1/auth/login
```

Purpose

Authenticate a student.

---

## Logout

Method

POST

Endpoint

```text id="qtkzqp"
/api/v1/auth/logout
```

Purpose

Terminate the current session.

---

# 6. Student Profile APIs

## Get Student Profile

Method

GET

Endpoint

```text id="f2g6u5"
/api/v1/profile
```

Purpose

Return the current student profile.

---

## Update Student Profile

Method

PUT

Endpoint

```text id="zv5zri"
/api/v1/profile
```

Purpose

Update editable profile information.

---

# 7. Assessment APIs

## Submit Assessment

Method

POST

Endpoint

```text id="9g0t1m"
/api/v1/assessment
```

Purpose

Submit assessment results.

Workflow

Learning Orchestrator

↓

Student Profile

↓

Recommendation Engine

---

## Get Assessment Result

Method

GET

Endpoint

```text id="wlbktl"
/api/v1/assessment/result
```

Purpose

Retrieve the latest assessment result.

---

# 8. Learning Plan APIs

## Generate Learning Plan

Method

POST

Endpoint

```text id="vmzcg3"
/api/v1/plan/generate
```

Purpose

Generate a personalized learning plan.

Workflow

Learning Orchestrator

↓

Recommendation Engine

---

## Get Current Learning Plan

Method

GET

Endpoint

```text id="rj31bi"
/api/v1/plan/current
```

Purpose

Retrieve the current learning plan.

---

# 9. AI Chat APIs

## Chat

Method

POST

Endpoint

```text id="t6bax0"
/api/v1/chat
```

Purpose

Submit a learning question.

Workflow

Learning Orchestrator

↓

Student Profile

↓

RAG Module

↓

LLM Service

---

## Get Chat History

Method

GET

Endpoint

```text id="pqv8nt"
/api/v1/chat/history
```

Purpose

Retrieve historical conversations.

---

# 10. Learning Progress APIs

## Complete Learning Task

Method

POST

Endpoint

```text id="i7jybz"
/api/v1/learning/complete
```

Purpose

Submit learning completion.

Workflow

Learning Orchestrator

↓

Student Profile

↓

Recommendation Engine

---

## Get Learning Progress

Method

GET

Endpoint

```text id="1u3f2x"
/api/v1/learning/progress
```

Purpose

Retrieve learning progress.

---

# 11. Resource APIs

## Search Learning Resources

Method

GET

Endpoint

```text id="twv6rk"
/api/v1/resources/search
```

Purpose

Search educational resources.

Workflow

Learning Orchestrator

↓

RAG Module

---

## Get Resource Details

Method

GET

Endpoint

```text id="4o3xja"
/api/v1/resources/{resource_id}
```

Purpose

Retrieve detailed information for a learning resource.

---

# 12. Health Check API

Method

GET

Endpoint

```text id="v86g2j"
/api/v1/health
```

Purpose

Check system availability.

Returns

* API status
* Database status
* LLM status
* Vector database status

---

# 13. HTTP Status Codes

| Code | Meaning               |
| ---- | --------------------- |
| 200  | Success               |
| 201  | Resource Created      |
| 400  | Invalid Request       |
| 401  | Unauthorized          |
| 403  | Forbidden             |
| 404  | Resource Not Found    |
| 500  | Internal Server Error |

---

# 14. API Rules

Every API must satisfy the following rules.

* Validate input.
* Return standardized JSON.
* Never expose database models.
* Never execute business logic.
* Always call the Learning Orchestrator.

---

# 15. API Versioning

Current Version

```text id="v0dzpp"
v1
```

Future versions

```text id="dzk2yk"
/api/v2
/api/v3
```

New versions must maintain backward compatibility whenever possible.

---

# 16. Summary

The API layer serves as the communication gateway between the frontend and backend.

Its responsibilities are limited to:

* Receiving requests
* Validating requests
* Calling the Learning Orchestrator
* Returning standardized responses

No business logic is permitted within the API layer.

---

# 17. Next Document

Next:

07_Development_Roadmap.md

This document defines the complete development sequence, implementation milestones, and engineering roadmap for EduMind V1.
