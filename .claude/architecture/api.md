# API Architecture Principles

The backend is built using FastAPI.

Design rules:
- RESTful APIs with clear resource boundaries
- Explicit request and response schemas
- Validation at API boundaries
- Business logic separated from routing

When designing endpoints:
- Explain what problem the endpoint solves
- Describe the data flow
- Explain how errors are handled
- Consider versioning implications

Avoid tightly coupling endpoints to frontend assumptions.