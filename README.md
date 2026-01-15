# Shotgun ENSAI - Event Booking Platform

![Python](https://img.shields.io/badge/Python-3.13-blue) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-DB-blue) ![Architecture](https://img.shields.io/badge/Architecture-DAO%2FService%2FView-green) ![Docker](https://img.shields.io/badge/Container-Docker-blue)

## Project Overview
Shotgun ENSAI is a robust **CLI (Command Line Interface)** application designed to manage student event reservations in real-time. Developed as part of the 2nd-year Engineering curriculum at **ENSAI**, it demonstrates software development best practices through a complete event management workflow.

Unlike simple scripts, this project implements a strict **Multi-Layer Architecture** (View, Service, DAO) to ensure scalability, security, and maintainability.

## Technical Architecture & Features
The application follows a modular architecture described in the provided technical report:

* **DAO (Data Access Object):** Manages secure database access and optimized SQL queries.
* **Service Layer:** Handles business logic, ACID transactions (commit/rollback), and process validation.
* **View Layer:** Interactive command-line interface built with `InquirerPy`.
* **External Integration:** Automated email notifications via **Brevo API**.
* **Security:** Password hashing (`bcrypt`) and protection against SQL injections.

## How to Run (The Easy Way: Docker)
You don't need to install Python or PostgreSQL locally. Just use Docker.

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/khalidjerrari/ENSAI-Projet-info-2A.git](https://github.com/khalidjerrari/ENSAI-Projet-info-2A.git)
    cd ENSAI-Projet-info-2A
    ```

2.  **Run with Docker Compose**
    ```bash
    docker-compose up --build
    ```
    *This will start the Database and the Application automatically.*

## How to Run (Manual Installation)
If you prefer running it without Docker (e.g., for development on VSCode):

1.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Configure Database**
    * Create a `.env` file at the root (see `.env.example`).
    * Ensure you have a PostgreSQL instance running.
3.  **Run the App**
    ```bash
    python src/main.py
    ```

## Testing & Quality
The project includes a comprehensive test suite using `pytest`.

* **Run All Tests:**
    ```bash
    pytest -v
    ```
* **Check Test Coverage:**
    ```bash
    coverage run -m pytest
    coverage report -m
    ```
* **CI/CD:** A GitHub Actions pipeline automatically analyzes code quality (`pylint`) and runs tests on each push.

## Project Structure
The source code is organized in a strict layered architecture:

```text
├── src
│   ├── business_object  # Domain entities
│   ├── dao              # Database interactions (SQL)
│   ├── service          # Business logic & Rules
│   ├── view             # Console UI (InquirerPy)
│   ├── model            # Pydantic models (Input/Output)
│   └── utils            # Helpers (DB Connection, Security)
├── data                 # SQL initialization scripts
├── tests                # Unit and Integration tests
├── Dockerfile           # Container definition
└── docker-compose.yml   # Orchestration
