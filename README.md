# Hungry AI

**Feed it data. It remembers.**

Hungry AI is a local AI agent powered by Ollama LLMs that becomes more personalized with every piece of information you provide.

Give it your documents, notes, PDFs, websites, codebases, research, and knowledge sources. Hungry AI scans, crawls, indexes, and remembers what it learns, building a private knowledge base tailored specifically to you.

Your AI becomes more useful over time—understanding your projects, interests, workflows, and domain knowledge instead of relying solely on a generic language model.

> **Your data stays your data.** Everything runs locally and remains under your control.

---

## Features

* 🖥️ Runs locally using Ollama LLMs
* 📄 Ingests documents, notes, and PDFs
* 🌐 Crawls websites and online resources
* 🧠 Builds a personalized knowledge base from your data
* 🔍 Retrieves relevant information when answering questions
* 🔗 Combines retrieval with LLM reasoning (RAG)
* 📚 Learns from both local files and web content
* 🔒 Keeps your data on your machine

---

## How It Works

Hungry AI uses **Retrieval-Augmented Generation (RAG)** to search, retrieve, and reason over external knowledge sources before generating responses.

Instead of depending only on an LLM's built-in knowledge, Hungry AI can:

1. Ingest your data
2. Index and organize it
3. Retrieve relevant information when needed
4. Generate context-aware answers grounded in your knowledge base

The more you feed Hungry AI, the more personalized and useful it becomes.

---

## Setup

### Install Dependencies

```bash
pip install -r reqs.txt
```

### PostgreSQL Setup

```bash
sudo -u postgres psql

CREATE DATABASE ragdb;

CREATE USER raguser WITH PASSWORD 'ragpass';

GRANT ALL PRIVILEGES ON DATABASE ragdb TO raguser;
```

---

## Usage

### Main Application

Run:

```bash
python main.py
```

Available commands:

| Command   | Description                        |
| --------- | ---------------------------------- |
| `/help`   | Show available commands            |
| `/info`   | Display system information         |
| `/clear`  | Clear conversation history         |
| `/list`   | List stored knowledge categories   |
| `/docs`   | Show documentation                 |
| `/status` | Display database and system status |
| `/exit`   | Exit Hungry AI                     |

---

### Data Ingestion

Run:

```bash
python ingest.py --help
```

#### Ingest Web Content

```bash
python ingest.py --mode web --url <URL>
```

#### Ingest Documents

```bash
python ingest.py --mode docs --path <PATH>
```

---

## Ingestion Options

| Option                   | Description                                |
| ------------------------ | ------------------------------------------ |
| `--concurrency <number>` | Number of parallel requests (default: `8`) |
| `--delay <seconds>`      | Delay between requests (default: `0.5`)    |
| `--crawl`                | Follow and crawl discovered links          |
| `--max-pages <number>`   | Maximum pages to crawl                     |

### Example

```bash
python ingest.py \
  --mode web \
  --url https://example.com \
  --crawl \
  --max-pages 50 \
  --concurrency 8
```

---

## Memory Management

### Check Database Status

```bash
python ingest.py --check
```

### Browse Stored Knowledge

List all categories:

```text
list
```

View a specific category:

```text
list <category>
```

Remove empty entries:

```text
list --a
```

### Delete Data

Remove an entire category:

```text
remove <category>
```

Remove a specific record by ID:

```text
remove <category> <id>
```

Delete a subcategory:

```text
delete subcategory <category> <subcategory>
```

---

## Why Hungry AI?

Most AI assistants start every conversation with the same generic knowledge.

Hungry AI is different.

By continuously ingesting and retrieving information from your documents, websites, codebases, notes, and research, it develops a knowledge base unique to you. The result is an AI assistant that understands your work, remembers what matters, and provides answers grounded in your own data.

**Feed it data. It remembers.**

