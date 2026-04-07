# Nadiaris Labs: AI-Powered Threat Audit API 🛡️

Nadiaris Labs is a production-grade cybersecurity backend designed to perform deep semantic analysis of code snippets. Unlike traditional static analysis, Nadiaris uses **Large Language Models (LLMs)** to identify malicious intent, such as "wiper" malware, logic bombs, and obfuscated data exfiltration.

## 🚀 Key Features

* **AI-Driven Audits:** Leverages **Google Gemini 2.5 Flash** to reason about code behavior and destructive payloads.
* **High-Performance Caching:** Integrated **Redis 7** cache-aside pattern reduces repeat scan latency from **7s to <5ms**.
* **The Vault (Audit Logging):** Every scan is permanently logged in **PostgreSQL 16** with UUIDs, latency tracking, and severity grading.
* **Asynchronous Architecture:** Built with **FastAPI** and `asyncpg` to handle high-concurrency requests without blocking.
* **Containerized Environment:** Fully orchestrated using **Podman/Docker** for seamless deployment and environment parity.

## 🛠️ Tech Stack

* **Framework:** FastAPI (Python 3.11)
* **AI Engine:** Google Gemini Pro API
* **Database:** PostgreSQL 16
* **Cache:** Redis 7
* **Infrastructure:** Podman & Podman-Compose
* **ORM:** SQLAlchemy 2.0 (Async)

## 📦 Infrastructure Setup

Ensure you have **Podman** or **Docker** installed, then spin up the infrastructure:

```bash
# Start the Database and Cache
podman-compose up -d
```

## ⚙️ Installation & Running

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/nadiaris-labs.git](https://github.com/your-username/nadiaris-labs.git)
    cd nadiaris-labs
    ```

2.  **Set up the environment:**
    Create a `.env` file in the root directory:
    ```env
    DATABASE_URL=postgresql+asyncpg://postgres:ahu123@127.0.0.1:5432/threat_audit
    GEMINI_API_KEY=your_google_gemini_api_key
    REDIS_URL=redis://127.0.0.1:6379/0
    ```

3.  **Install dependencies:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```

4.  **Run the server:**
    ```bash
    uvicorn main:app --reload
    ```

## 🔍 API Usage

Access the interactive documentation at: `http://127.0.0.1:8000/docs`

### Scan Code Snippet
**POST** `/api/v1/scan`

**Request Body:**
```json
{
  "code_snippet": "import os\nos.system('rm -rf /')"
}
```

**Response:**
```json
{
  "status": "success",
  "log_id": "42496cc9-efa6-48a0-b530-57026a763232",
  "latency_ms": 7172.44,
  "analysis": "CRITICAL: Malicious intent detected. Payload identified as a 'disk wiper'..."
}
```

## 🛣️ Roadmap

- [ ] **Phase 6:** Integrate **AMD Vitis AI** for local INT8 hardware-accelerated scanning.
- [ ] **Phase 7:** Implement JWT-based Authentication & Rate Limiting.
- [ ] **Phase 8:** Deploy to **Microsoft Azure** using Container Instances.

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.

