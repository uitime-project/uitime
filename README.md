# uitime.

![.NET Core](https://img.shields.io/badge/.NET%20Core-512BD4?style=for-the-badge&logo=dotnet&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Telegram API](https://img.shields.io/badge/Telegram_API-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)

A stateless, containerized microservice architecture built to demonstrate high-performance data processing, secure token-based authentication, and seamless integration between a RESTful API and a messaging-platform worker.

> **Note:** This repository is currently in the MVP phase for an academic engineering project. Specific business logic and domain details have been abstracted in this documentation.

## 🚀 Technical Overview

The system is designed with a strong emphasis on the **Separation of Concerns** and **Stateless Architecture**, allowing it to survive ephemeral cloud environments (cold starts) while maintaining data integrity and session continuity.

### Stack & Infrastructure
* **Backend Core (REST API):** C# / ASP.NET Core
* **Worker Service (Bot Interface):** Python 3 / `aiogram 3`
* **Database:** PostgreSQL (Neon) with Entity Framework Core (ORM)
* **Session Cache:** SQLite (Local worker storage)
* **DevOps:** Docker, Docker Compose, GitHub Actions (CI/CD)

## ⚙️ Key Architectural Features

* **JWT Authentication Bridge:** Cross-service authentication is handled via JSON Web Tokens. A lightweight web interface generates secure access codes, which are then exchanged by the Python worker to authenticate requests to the C# backend.
* **Webhook Architecture:** The Python worker utilizes a Webhook-based approach instead of Long Polling, drastically reducing idle resource consumption and optimizing cloud deployment costs.
* **Resilient State Management:** To counteract "session amnesia" during container restarts, user states (FSM) within the worker are cached in a lightweight SQLite database, ensuring uninterrupted user flows.
* **Asynchronous Processing:** Deeply integrated `async/await` patterns across both the C# API and Python worker to prevent thread-blocking during heavy file parsing and database transactions.
* **Infrastructure as Code (IaC):** Fully containerized setup allowing the entire multi-node system to be spun up locally with a single `docker-compose` command.

## 💻 Local Development Setup

To run the microservices locally, ensure you have Docker and Docker Compose installed.
