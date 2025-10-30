
# 🧠 Diagnostic System for Web Crawlers

A **distributed diagnostic system** designed to enhance web crawler efficiency and data yield for **Large Language Model (LLM)** training.
This project autonomously analyzes URLs before crawling to detect potential issues such as `robots.txt` restrictions, SSL errors, and missing sitemaps — **without running a full crawl**.

---

## 📘 Overview

Web crawlers often fail due to server restrictions, dynamic content, or misconfigurations, leading to incomplete data collection.
This diagnostic system introduces a **pre-crawl diagnostic layer** that independently evaluates URLs, classifies errors, and provides actionable feedback — improving crawl success rates and resource efficiency.

### ✨ Key Features

* **Pre-Crawl Diagnostics** – Detects issues before crawling (robots.txt, SSL, sitemap, Cloudflare blocks).
* **Distributed Architecture** – Scales horizontally across multiple worker nodes using Redis.
* **Parallel Processing** – Multi-threaded and Redlock-based locking ensures consistent job handling.
* **REST API** – Flask-based API interface for submitting and retrieving diagnostics.
* **User Interface** – Intuitive web UI to input URLs and visualize color-coded results.
* **Containerized Deployment** – Easily deployable using Docker.

---

## 🧩 System Architecture

```
User → Flask API → Redis Queue → Workers → Diagnostic Modules → Aggregator → UI / External Systems
```

### Components

| File                   | Description                                                           |
| ---------------------- | --------------------------------------------------------------------- |
| **app.py**             | Flask web server with REST API endpoints and UI routes.               |
| **diagnose_module.py** | Core diagnostic logic (robots.txt, sitemap, SSL, server checks).      |
| **worker.py**          | Worker process fetching and diagnosing URLs from Redis queue.         |
| **redis_q.py**         | Queue management and distributed task orchestration.                  |
| **utils.py**           | Helper utilities for parsing, logging, and formatting.                |
| **Dockerfile**         | Container definition for running the system in isolated environments. |

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/<your-repo>/web-diagnostic-system.git
cd web-diagnostic-system
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**

* Flask
* Redis
* Requests
* BeautifulSoup4
* xmltodict
* redlock-py

---

## 🚀 Usage

### 1. Start Redis

Make sure Redis is running locally or remotely:

```bash
redis-server
```

### 2. Run the Flask App

```bash
python app.py
```

### 3. Start Worker(s)

```bash
python worker.py
```

### 4. Access the Web UI

Open your browser and navigate to:

```
http://localhost:5000
```

### 5. Submit URLs

* Enter one or more URLs in the UI input box.
* The system performs diagnostics asynchronously.
* Results appear color-coded:

  * 🟢 Success
  * 🟡 Warning (e.g., unparseable sitemap)
  * 🔴 Error (e.g., SSL or robots.txt block)

---

## 🧱 Docker Deployment

Build and run using Docker:

```bash
docker build -t crawler-diagnostic .
docker run -p 5000:5000 crawler-diagnostic
```

You can also orchestrate Redis and workers with Docker Compose.

---

## 📊 Evaluation Highlights

Based on system tests (100 URLs, 5 distributed nodes):

* Diagnosed **>60%** of previously unknown crawl failures.
* Identified major error clusters:

  * `robots.txt` violations
  * SSL certificate errors
  * Missing or malformed sitemaps
* Improved data collection yield and reduced resource waste.

---

## 📈 Research Context

This project was developed as part of the thesis:

> **“A Diagnostic System for Enhancing Web Crawler Yield and Efficiency for Large Language Models”**
> *Abdulaziz Al-Surabi, DHBW Stuttgart, 2025*

It applies the **Design Science Research (DSR)** methodology to develop an artifact that addresses real-world inefficiencies in large-scale web crawling for LLM data acquisition.

---

## 📂 Future Work

* Add diagnostics for dynamic JavaScript-rendered pages.
* Integrate AI-based pattern recognition for adaptive retry strategies.
* Expand visualization with performance analytics dashboards.

---

## 🧑‍💻 Authors

**Abdulaziz Al-Surabi**
Faculty of Economics and Health — DHBW Stuttgart
IBM Almaden Research Center

Supervisor: **Prof. Dr. Kai Holzweißig**, DHBW Stuttgart
Research Advisor: **Dr. Yi Zhou**, IBM Research

---
