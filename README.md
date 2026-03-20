# genai-driven-fastapi-testing
A cloud‑native test automation framework combining FastAPI and Robot Framework, enhanced with Generative AI to create diverse test suites from templates. Features modular APIs, data‑driven testing without databases, Dockerized deployment, and CI/CD integration via GitHub Actions.

# fastapi-robot-genai-tests

A cloud-native test automation framework combining FastAPI and Robot Framework, enhanced with Generative AI for dynamic test suite generation.

## Quick Start
```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
robot robot-tests/suites
```

## Features
- FastAPI backend
- Robot Framework test suites
- Data-driven testing without databases
- CI/CD with GitHub Actions
- Dockerized deployment
