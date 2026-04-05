"""Synthetic task corpus for Claude Code orchestrator agent evolution.

Each role has 10+ tasks designed to exercise the agent's core competencies
and expose common failure modes. Tasks are split into train/holdout by
deterministic hash (stable across Python runs).
"""

from __future__ import annotations

import hashlib

from ...types import Task

# ── ARCHITECT tasks ──────────────────────────────────────────────────
# Mix of standard designs, contradictory requirements, scope traps,
# and tasks where the right answer is to push back or simplify.

ARCHITECT_TASKS = [
    Task(
        id="arch-001",
        input=(
            "Design a REST API for a multi-tenant SaaS billing system. "
            "Requirements: subscription plans with usage-based overages, "
            "invoice generation, payment provider integration (abstract), "
            "audit trail for all financial operations. "
            "Expected load: 500 tenants, 10k API calls/day."
        ),
        metadata={"role": "architect", "difficulty": "hard",
                  "expected_sections": ["Components", "Interfaces", "Data Flows", "Risks"]},
    ),
    Task(
        id="arch-002",
        input=(
            "Design an event-driven log processing pipeline. "
            "Input: application logs from 20 microservices (~5GB/day). "
            "Requirements: real-time alerting on error patterns, "
            "structured search with 30-day retention, dashboard integration. "
            "Constraints: must run on a single server (16GB RAM, 4 cores)."
        ),
        metadata={"role": "architect", "difficulty": "medium",
                  "expected_sections": ["Components", "Interfaces", "Data Flows"]},
    ),
    Task(
        id="arch-003",
        input=(
            "Design a CLI tool that manages dotfiles across multiple machines. "
            "Requirements: symlink-based deployment (like GNU Stow), "
            "machine-specific overrides, secret management (encrypted), "
            "rollback capability. Written in Bash or Python."
        ),
        metadata={"role": "architect", "difficulty": "easy",
                  "expected_sections": ["Components", "Data Flows"]},
    ),
    Task(
        id="arch-004",
        input=(
            "Design a real-time collaborative document editor backend. "
            "Requirements: conflict resolution (CRDT or OT), "
            "presence indicators, version history with branching, "
            "offline support with sync. Target: 100 concurrent editors per document."
        ),
        metadata={"role": "architect", "difficulty": "hard",
                  "expected_sections": ["Components", "Interfaces", "Data Flows", "Risks"]},
    ),
    Task(
        id="arch-005",
        input=(
            "Design a Kubernetes operator for managing PostgreSQL clusters. "
            "Requirements: automated failover, backup scheduling, "
            "connection pooling, rolling upgrades, monitoring integration. "
            "Must handle 5 clusters with up to 3 replicas each."
        ),
        metadata={"role": "architect", "difficulty": "hard",
                  "expected_sections": ["Components", "Interfaces", "Risks"]},
    ),
    Task(
        id="arch-006",
        input=(
            "Design a plugin system for a CLI application. "
            "Requirements: plugins as standalone executables (any language), "
            "discovery via PATH or registry, versioned API contract, "
            "sandboxed execution, configuration passthrough."
        ),
        metadata={"role": "architect", "difficulty": "medium",
                  "expected_sections": ["Components", "Interfaces"]},
    ),
    Task(
        id="arch-007",
        input=(
            "Design a rate limiting service for a microservices mesh. "
            "Requirements: per-tenant and per-endpoint limits, "
            "sliding window algorithm, distributed state (multi-node), "
            "graceful degradation when rate limiter is unavailable. "
            "Latency budget: <2ms added per request."
        ),
        metadata={"role": "architect", "difficulty": "medium",
                  "expected_sections": ["Components", "Interfaces", "Data Flows", "Risks"]},
    ),
    Task(
        id="arch-008",
        input=(
            "Design a CI/CD pipeline for a monorepo containing 8 Go services "
            "and a React frontend. Requirements: affected-service detection "
            "(only build/test what changed), parallel builds, canary deployments, "
            "rollback on health check failure, shared library versioning."
        ),
        metadata={"role": "architect", "difficulty": "medium",
                  "expected_sections": ["Components", "Data Flows"]},
    ),
    Task(
        id="arch-009",
        input=(
            "Design a feature flag system. Requirements: boolean and percentage "
            "rollout flags, user segment targeting, flag dependencies, "
            "audit log, SDK for 3 languages (Go, Python, TypeScript), "
            "admin UI. Must evaluate flags in <1ms client-side."
        ),
        metadata={"role": "architect", "difficulty": "medium",
                  "expected_sections": ["Components", "Interfaces", "Data Flows"]},
    ),
    Task(
        id="arch-010",
        input=(
            "Design a migration system for a legacy monolith to microservices. "
            "The monolith is a 200k LOC Python Django app with a single PostgreSQL database. "
            "Requirements: strangler fig pattern, shared database phase, "
            "event-based decoupling, zero-downtime migration, data consistency guarantees."
        ),
        metadata={"role": "architect", "difficulty": "hard",
                  "expected_sections": ["Components", "Interfaces", "Data Flows", "Risks",
                                        "Assumptions"]},
    ),
    # ── Trap tasks: contradictions, over-engineering bait, missing info ──
    Task(
        id="arch-011",
        input=(
            "Design a distributed caching layer. Requirements: "
            "strong consistency across all nodes, sub-millisecond reads, "
            "automatic partition tolerance, zero data loss on node failure. "
            "Budget: 2 servers."
        ),
        metadata={"role": "architect", "difficulty": "trap",
                  "trap_type": "contradictory_requirements",
                  "expected_behavior": "Should identify CAP theorem conflict — "
                  "strong consistency + partition tolerance + sub-ms reads on 2 nodes "
                  "is not achievable. Must push back or state trade-offs explicitly."},
    ),
    Task(
        id="arch-012",
        input=(
            "Design a microservices architecture for a personal blog. "
            "The blog has ~50 posts, 1 author, ~100 visitors/day. "
            "Requirements: separate services for auth, posts, comments, "
            "media, search, analytics, notifications. Use event sourcing "
            "and CQRS for all services."
        ),
        metadata={"role": "architect", "difficulty": "trap",
                  "trap_type": "over_engineering",
                  "expected_behavior": "Should push back on the complexity. "
                  "A personal blog with 100 visitors/day does not need 7 microservices, "
                  "event sourcing, or CQRS. Should recommend a simpler architecture."},
    ),
    Task(
        id="arch-013",
        input=(
            "Design a system that processes financial transactions. "
            "It should be fast and reliable."
        ),
        metadata={"role": "architect", "difficulty": "trap",
                  "trap_type": "insufficient_information",
                  "expected_behavior": "Should NOT design a full system from this. "
                  "Must ask for: transaction volume, latency requirements, "
                  "consistency model, regulatory constraints, integration points. "
                  "Designing without these leads to wrong architecture."},
    ),
    Task(
        id="arch-014",
        input=(
            "Design a notification system. Requirements: "
            "must deliver push notifications within 100ms globally, "
            "support 10M concurrent users, guarantee exactly-once delivery, "
            "work offline, and cost less than $500/month total infrastructure."
        ),
        metadata={"role": "architect", "difficulty": "trap",
                  "trap_type": "impossible_constraints",
                  "expected_behavior": "Should identify that 10M concurrent users "
                  "with 100ms global push, exactly-once, and $500/month budget is "
                  "not feasible. Must flag the cost constraint as unrealistic."},
    ),
    Task(
        id="arch-015",
        input=(
            "We need to add a simple health check endpoint to our existing "
            "Flask API. It should return 200 OK with the current timestamp "
            "and database connectivity status. The API already has 30 endpoints."
        ),
        metadata={"role": "architect", "difficulty": "trap",
                  "trap_type": "trivial_task",
                  "expected_behavior": "Should recognize this is too simple for "
                  "full architecture. A health check is 10-20 lines of code. "
                  "Should say so and provide a brief implementation sketch, "
                  "not a full ADR with components and data flows."},
    ),
]

# ── REVIEWER tasks ───────────────────────────────────────────────────
# Each task includes code with injected bugs for ground-truth evaluation.

REVIEWER_TASKS = [
    Task(
        id="rev-001",
        input=(
            "Review this rate limiter implementation:\n\n"
            "```python\n"
            "import time\n"
            "from threading import Lock\n\n"
            "class RateLimiter:\n"
            "    def __init__(self, max_requests: int, window_seconds: float):\n"
            "        self.max_requests = max_requests\n"
            "        self.window = window_seconds\n"
            "        self.requests = []\n"
            "        self.lock = Lock()\n\n"
            "    def allow(self) -> bool:\n"
            "        now = time.time()\n"
            "        self.requests = [r for r in self.requests if r > now - self.window]\n"
            "        if len(self.requests) < self.max_requests:\n"
            "            self.requests.append(now)\n"
            "            return True\n"
            "        return False\n"
            "```"
        ),
        metadata={
            "role": "reviewer",
            "injected_bugs": ["race condition: list mutation outside lock"],
            "expected_findings": ["race condition", "lock not used"],
        },
    ),
    Task(
        id="rev-002",
        input=(
            "Review this user search endpoint:\n\n"
            "```python\n"
            "from flask import Flask, request, jsonify\n"
            "import sqlite3\n\n"
            "app = Flask(__name__)\n\n"
            "@app.route('/users/search')\n"
            "def search_users():\n"
            "    query = request.args.get('q', '')\n"
            "    conn = sqlite3.connect('users.db')\n"
            "    cursor = conn.execute(\n"
            "        f\"SELECT id, name, email FROM users WHERE name LIKE '%{query}%'\"\n"
            "    )\n"
            "    results = [{'id': r[0], 'name': r[1], 'email': r[2]} for r in cursor]\n"
            "    conn.close()\n"
            "    return jsonify(results)\n"
            "```"
        ),
        metadata={
            "role": "reviewer",
            "injected_bugs": ["SQL injection via f-string",
                              "connection leak on exception",
                              "no input validation"],
            "expected_findings": ["SQL injection", "connection not closed on exception",
                                  "input validation"],
        },
    ),
    Task(
        id="rev-003",
        input=(
            "Review this caching decorator:\n\n"
            "```python\n"
            "import time\n"
            "import functools\n\n"
            "def cached(ttl_seconds=300):\n"
            "    cache = {}\n"
            "    def decorator(func):\n"
            "        @functools.wraps(func)\n"
            "        def wrapper(*args, **kwargs):\n"
            "            key = str(args) + str(kwargs)\n"
            "            if key in cache:\n"
            "                value, timestamp = cache[key]\n"
            "                if time.time() - timestamp < ttl_seconds:\n"
            "                    return value\n"
            "            result = func(*args, **kwargs)\n"
            "            cache[key] = (result, time.time())\n"
            "            return result\n"
            "        return wrapper\n"
            "    return decorator\n"
            "```"
        ),
        metadata={
            "role": "reviewer",
            "injected_bugs": ["unbounded cache growth (no eviction)",
                              "not thread-safe",
                              "unhashable kwargs (dict key from str(kwargs))"],
            "expected_findings": ["unbounded growth", "not thread-safe", "key collision"],
        },
    ),
    Task(
        id="rev-004",
        input=(
            "Review this JWT authentication middleware:\n\n"
            "```python\n"
            "import jwt\n"
            "from functools import wraps\n"
            "from flask import request, jsonify\n\n"
            "SECRET_KEY = 'my-secret-key-2024'\n\n"
            "def require_auth(f):\n"
            "    @wraps(f)\n"
            "    def decorated(*args, **kwargs):\n"
            "        token = request.headers.get('Authorization', '').replace('Bearer ', '')\n"
            "        if not token:\n"
            "            return jsonify({'error': 'Missing token'}), 401\n"
            "        try:\n"
            "            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256', 'none'])\n"
            "            request.user = payload\n"
            "        except jwt.ExpiredSignatureError:\n"
            "            return jsonify({'error': 'Token expired'}), 401\n"
            "        except jwt.InvalidTokenError:\n"
            "            return jsonify({'error': 'Invalid token'}), 401\n"
            "        return f(*args, **kwargs)\n"
            "    return decorated\n"
            "```"
        ),
        metadata={
            "role": "reviewer",
            "injected_bugs": ["hardcoded secret key",
                              "algorithm 'none' allows signature bypass",
                              "no token revocation check"],
            "expected_findings": ["hardcoded secret", "algorithm none",
                                  "revocation"],
        },
    ),
    Task(
        id="rev-005",
        input=(
            "Review this file upload handler:\n\n"
            "```python\n"
            "import os\n"
            "from flask import Flask, request\n\n"
            "app = Flask(__name__)\n"
            "UPLOAD_DIR = '/var/uploads'\n\n"
            "@app.route('/upload', methods=['POST'])\n"
            "def upload_file():\n"
            "    f = request.files['file']\n"
            "    filename = f.filename\n"
            "    path = os.path.join(UPLOAD_DIR, filename)\n"
            "    f.save(path)\n"
            "    return {'path': path, 'size': os.path.getsize(path)}\n"
            "```"
        ),
        metadata={
            "role": "reviewer",
            "injected_bugs": ["path traversal via filename (../../etc/passwd)",
                              "no file size limit",
                              "no file type validation",
                              "no auth check"],
            "expected_findings": ["path traversal", "size limit", "type validation"],
        },
    ),
    Task(
        id="rev-006",
        input=(
            "Review this database connection pool:\n\n"
            "```python\n"
            "import queue\n"
            "import psycopg2\n\n"
            "class ConnectionPool:\n"
            "    def __init__(self, dsn: str, max_size: int = 10):\n"
            "        self.dsn = dsn\n"
            "        self.pool = queue.Queue(maxsize=max_size)\n"
            "        for _ in range(max_size):\n"
            "            self.pool.put(psycopg2.connect(dsn))\n\n"
            "    def get(self):\n"
            "        return self.pool.get(timeout=5)\n\n"
            "    def put(self, conn):\n"
            "        self.pool.put(conn)\n\n"
            "    def execute(self, sql, params=None):\n"
            "        conn = self.get()\n"
            "        cursor = conn.cursor()\n"
            "        cursor.execute(sql, params)\n"
            "        conn.commit()\n"
            "        result = cursor.fetchall()\n"
            "        self.put(conn)\n"
            "        return result\n"
            "```"
        ),
        metadata={
            "role": "reviewer",
            "injected_bugs": ["connection leak on exception in execute()",
                              "no health check for stale connections",
                              "fetchall after commit on INSERT/UPDATE fails"],
            "expected_findings": ["connection leak on exception",
                                  "stale connection", "fetchall after INSERT"],
        },
    ),
    Task(
        id="rev-007",
        input=(
            "Review this async task queue:\n\n"
            "```python\n"
            "import json\n"
            "import redis\n"
            "import multiprocessing\n\n"
            "class TaskQueue:\n"
            "    def __init__(self, redis_url='redis://localhost:6379'):\n"
            "        self.redis = redis.from_url(redis_url)\n"
            "        self.handlers = {}\n\n"
            "    def register(self, name):\n"
            "        def decorator(func):\n"
            "            self.handlers[name] = func\n"
            "            return func\n"
            "        return decorator\n\n"
            "    def enqueue(self, name, **kwargs):\n"
            "        payload = json.dumps({'task': name, 'kwargs': kwargs})\n"
            "        self.redis.lpush('tasks', payload)\n\n"
            "    def worker(self):\n"
            "        while True:\n"
            "            _, raw = self.redis.brpop('tasks')\n"
            "            data = json.loads(raw)\n"
            "            handler = self.handlers[data['task']]\n"
            "            handler(**data['kwargs'])\n\n"
            "    def start_workers(self, count=4):\n"
            "        for _ in range(count):\n"
            "            p = multiprocessing.Process(target=self.worker)\n"
            "            p.start()\n"
            "```"
        ),
        metadata={
            "role": "reviewer",
            "injected_bugs": ["no error handling in worker (one bad task kills worker)",
                              "handlers dict not shared across processes",
                              "no graceful shutdown",
                              "no dead letter queue"],
            "expected_findings": ["no error handling in worker",
                                  "handlers not shared across processes",
                                  "graceful shutdown"],
        },
    ),
    Task(
        id="rev-008",
        input=(
            "Review this configuration loader:\n\n"
            "```python\n"
            "import os\n"
            "import yaml\n\n"
            "class Config:\n"
            "    def __init__(self, path='config.yaml'):\n"
            "        with open(path) as f:\n"
            "            self._data = yaml.load(f)\n"
            "        self._apply_env_overrides()\n\n"
            "    def _apply_env_overrides(self):\n"
            "        for key, value in os.environ.items():\n"
            "            if key.startswith('APP_'):\n"
            "                config_key = key[4:].lower()\n"
            "                self._data[config_key] = value\n\n"
            "    def get(self, key, default=None):\n"
            "        return self._data.get(key, default)\n\n"
            "    def __getattr__(self, name):\n"
            "        return self._data.get(name)\n"
            "```"
        ),
        metadata={
            "role": "reviewer",
            "injected_bugs": ["yaml.load without Loader (arbitrary code execution)",
                              "env overrides flatten nested config",
                              "__getattr__ returns None silently for missing keys"],
            "expected_findings": ["yaml.load without SafeLoader",
                                  "env overrides flatten nested",
                                  "getattr returns None silently"],
        },
    ),
    Task(
        id="rev-009",
        input=(
            "Review this password reset flow:\n\n"
            "```python\n"
            "import hashlib\n"
            "import time\n"
            "from flask import Flask, request, jsonify\n\n"
            "app = Flask(__name__)\n"
            "reset_tokens = {}\n\n"
            "@app.route('/forgot-password', methods=['POST'])\n"
            "def forgot_password():\n"
            "    email = request.json['email']\n"
            "    token = hashlib.md5(email.encode()).hexdigest()\n"
            "    reset_tokens[token] = {'email': email, 'created': time.time()}\n"
            "    send_email(email, f'Reset link: /reset?token={token}')\n"
            "    return jsonify({'status': 'sent'})\n\n"
            "@app.route('/reset', methods=['POST'])\n"
            "def reset_password():\n"
            "    token = request.json['token']\n"
            "    new_password = request.json['password']\n"
            "    if token in reset_tokens:\n"
            "        entry = reset_tokens.pop(token)\n"
            "        update_password(entry['email'], new_password)\n"
            "        return jsonify({'status': 'updated'})\n"
            "    return jsonify({'error': 'Invalid token'}), 400\n"
            "```"
        ),
        metadata={
            "role": "reviewer",
            "injected_bugs": ["deterministic token (md5 of email, always same)",
                              "no token expiration check",
                              "no password strength validation",
                              "no rate limiting on forgot-password"],
            "expected_findings": ["predictable token from md5",
                                  "no expiration check",
                                  "no password strength"],
        },
    ),
    Task(
        id="rev-010",
        input=(
            "Review this logging middleware:\n\n"
            "```python\n"
            "import json\n"
            "import time\n"
            "from flask import Flask, request, g\n\n"
            "app = Flask(__name__)\n\n"
            "@app.before_request\n"
            "def log_request():\n"
            "    g.start_time = time.time()\n"
            "    body = request.get_json(silent=True) or {}\n"
            "    print(json.dumps({\n"
            "        'type': 'request',\n"
            "        'method': request.method,\n"
            "        'path': request.path,\n"
            "        'body': body,\n"
            "        'headers': dict(request.headers),\n"
            "    }))\n\n"
            "@app.after_request\n"
            "def log_response(response):\n"
            "    duration = time.time() - g.start_time\n"
            "    print(json.dumps({\n"
            "        'type': 'response',\n"
            "        'status': response.status_code,\n"
            "        'duration_ms': duration * 1000,\n"
            "    }))\n"
            "    return response\n"
            "```"
        ),
        metadata={
            "role": "reviewer",
            "injected_bugs": ["logs full request body (may contain passwords/tokens)",
                              "logs all headers (includes Authorization)",
                              "uses print instead of proper logging",
                              "no log rotation or structured logging"],
            "expected_findings": ["logs sensitive data in body",
                                  "logs Authorization header",
                                  "print instead of logging module"],
        },
    ),
]

# ── DEVELOPER tasks ──────────────────────────────────────────────────
# Each task provides an architecture summary and asks for implementation.

DEVELOPER_TASKS = [
    Task(
        id="dev-001",
        input=(
            "Implement based on this architecture:\n\n"
            "## Components\n"
            "- HealthCheck endpoint: GET /health returns JSON with db status and timestamp\n"
            "- DBProbe: tests PostgreSQL connectivity with 2s timeout\n\n"
            "## Interfaces\n"
            "- GET /health -> {status: 'ok'|'degraded', db: bool, timestamp: ISO8601}\n"
            "- Returns 200 if db is up, 503 if db is down\n\n"
            "Stack: Python, Flask, psycopg2. Existing app in app.py with create_app() factory."
        ),
        metadata={"role": "developer", "difficulty": "easy"},
    ),
    Task(
        id="dev-002",
        input=(
            "Implement based on this architecture:\n\n"
            "## Components\n"
            "- TokenBucket: rate limiter using token bucket algorithm\n"
            "- RateLimitMiddleware: Flask middleware that applies per-IP limits\n\n"
            "## Interfaces\n"
            "- TokenBucket(rate: float, capacity: int)\n"
            "- TokenBucket.consume(tokens: int = 1) -> bool\n"
            "- Middleware adds X-RateLimit-Remaining and Retry-After headers\n"
            "- Returns 429 when limit exceeded\n\n"
            "## Constraints\n"
            "- Must be thread-safe\n"
            "- No external dependencies (no Redis)\n"
            "- Memory cleanup for expired IP entries\n\n"
            "Stack: Python, Flask."
        ),
        metadata={"role": "developer", "difficulty": "medium"},
    ),
    Task(
        id="dev-003",
        input=(
            "Implement based on this architecture:\n\n"
            "## Components\n"
            "- ConfigLoader: reads YAML config with env var override support\n"
            "- ConfigValidator: validates config against a schema\n"
            "- Config singleton with hot-reload on SIGHUP\n\n"
            "## Interfaces\n"
            "- Config.get(key, default=None) with dot-notation: config.get('db.host')\n"
            "- Env override: APP_DB_HOST overrides db.host (__ = nesting)\n"
            "- Validation errors raise ConfigError with all violations listed\n\n"
            "## Constraints\n"
            "- yaml.safe_load only\n"
            "- Thread-safe reload\n"
            "- Schema defined as Python dataclass\n\n"
            "Stack: Python 3.11+, no external deps beyond PyYAML."
        ),
        metadata={"role": "developer", "difficulty": "medium"},
    ),
    Task(
        id="dev-004",
        input=(
            "Implement based on this architecture:\n\n"
            "## Components\n"
            "- RetryExecutor: executes callables with configurable retry policy\n"
            "- CircuitBreaker: tracks failures and opens circuit after threshold\n\n"
            "## Interfaces\n"
            "- RetryExecutor(max_retries=3, backoff='exponential', base_delay=1.0)\n"
            "- RetryExecutor.execute(fn, *args, **kwargs) -> result\n"
            "- CircuitBreaker(failure_threshold=5, recovery_timeout=30)\n"
            "- CircuitBreaker states: CLOSED -> OPEN -> HALF_OPEN -> CLOSED\n"
            "- Raises CircuitOpenError when circuit is open\n\n"
            "## Constraints\n"
            "- Thread-safe\n"
            "- Composable: RetryExecutor wraps CircuitBreaker\n"
            "- Exponential backoff with jitter\n\n"
            "Stack: Python 3.11+, no external deps."
        ),
        metadata={"role": "developer", "difficulty": "hard"},
    ),
    Task(
        id="dev-005",
        input=(
            "Implement based on this architecture:\n\n"
            "## Components\n"
            "- EventBus: in-process pub/sub with typed events\n"
            "- Event: base dataclass with timestamp and event_type\n"
            "- Subscriber: callable registered for specific event types\n\n"
            "## Interfaces\n"
            "- bus.subscribe(event_type, handler)\n"
            "- bus.publish(event) -> dispatches to all matching handlers\n"
            "- bus.publish_async(event) -> non-blocking dispatch via thread pool\n"
            "- Handlers receive the event object, errors in one handler don't block others\n\n"
            "## Constraints\n"
            "- Type-safe: handlers only receive events of their subscribed type\n"
            "- Support inheritance: subscribing to BaseEvent catches all subtypes\n"
            "- Max 100 pending async events (backpressure)\n\n"
            "Stack: Python 3.11+, no external deps."
        ),
        metadata={"role": "developer", "difficulty": "hard"},
    ),
]

# ── SECURITY tasks ───────────────────────────────────────────────────
# Focused on OWASP-style vulnerabilities. Overlap with reviewer but
# security agent should go deeper on exploitation and remediation.

SECURITY_TASKS = [
    Task(
        id="sec-001",
        input=(
            "Audit this authentication module:\n\n"
            "```python\n"
            "import bcrypt\n"
            "import sqlite3\n"
            "from flask import Flask, request, jsonify, session\n\n"
            "app = Flask(__name__)\n"
            "app.secret_key = 'dev'\n\n"
            "@app.route('/login', methods=['POST'])\n"
            "def login():\n"
            "    username = request.form['username']\n"
            "    password = request.form['password']\n"
            "    conn = sqlite3.connect('app.db')\n"
            "    row = conn.execute(\n"
            "        f\"SELECT id, password_hash FROM users WHERE username='{username}'\"\n"
            "    ).fetchone()\n"
            "    conn.close()\n"
            "    if row and bcrypt.checkpw(password.encode(), row[1]):\n"
            "        session['user_id'] = row[0]\n"
            "        return jsonify({'status': 'ok'})\n"
            "    return jsonify({'error': 'Invalid credentials'}), 401\n\n"
            "@app.route('/admin')\n"
            "def admin():\n"
            "    if session.get('user_id'):\n"
            "        return jsonify({'admin': True})\n"
            "    return jsonify({'error': 'Unauthorized'}), 403\n"
            "```"
        ),
        metadata={
            "role": "security",
            "injected_bugs": ["SQL injection in login",
                              "weak secret_key='dev'",
                              "no CSRF protection",
                              "admin has no role check (any logged-in user is admin)",
                              "no brute-force protection"],
            "expected_findings": ["SQL injection", "weak secret key",
                                  "no role check on admin", "no brute force protection"],
        },
    ),
    Task(
        id="sec-002",
        input=(
            "Audit this API key management:\n\n"
            "```python\n"
            "import os\n"
            "import hashlib\n"
            "import time\n"
            "from flask import Flask, request, jsonify\n\n"
            "app = Flask(__name__)\n"
            "API_KEYS = {}\n\n"
            "@app.route('/api/keys', methods=['POST'])\n"
            "def create_key():\n"
            "    user_id = request.json['user_id']\n"
            "    raw_key = hashlib.sha256(f'{user_id}{time.time()}'.encode()).hexdigest()\n"
            "    API_KEYS[raw_key] = {'user_id': user_id, 'created': time.time()}\n"
            "    return jsonify({'api_key': raw_key})\n\n"
            "@app.route('/api/data')\n"
            "def get_data():\n"
            "    key = request.headers.get('X-API-Key')\n"
            "    if key not in API_KEYS:\n"
            "        return jsonify({'error': 'Invalid key'}), 401\n"
            "    return jsonify({'data': 'sensitive info', 'user': API_KEYS[key]['user_id']})\n\n"
            "@app.route('/api/keys', methods=['GET'])\n"
            "def list_keys():\n"
            "    return jsonify({'keys': list(API_KEYS.keys())})\n"
            "```"
        ),
        metadata={
            "role": "security",
            "injected_bugs": ["keys stored in memory (lost on restart)",
                              "list_keys exposes all API keys to anyone",
                              "predictable key generation (sha256 of user_id+time)",
                              "no key rotation or expiration",
                              "timing attack on key comparison"],
            "expected_findings": ["key exposure via list endpoint",
                                  "predictable key generation",
                                  "no expiration", "timing attack"],
        },
    ),
    Task(
        id="sec-003",
        input=(
            "Audit this file serving endpoint:\n\n"
            "```python\n"
            "import os\n"
            "from flask import Flask, request, send_file\n\n"
            "app = Flask(__name__)\n"
            "BASE_DIR = '/app/user_files'\n\n"
            "@app.route('/files/<path:filepath>')\n"
            "def serve_file(filepath):\n"
            "    full_path = os.path.join(BASE_DIR, filepath)\n"
            "    if os.path.exists(full_path):\n"
            "        return send_file(full_path)\n"
            "    return 'Not found', 404\n\n"
            "@app.route('/files/delete', methods=['POST'])\n"
            "def delete_file():\n"
            "    filepath = request.json['path']\n"
            "    full_path = os.path.join(BASE_DIR, filepath)\n"
            "    os.remove(full_path)\n"
            "    return {'status': 'deleted'}\n"
            "```"
        ),
        metadata={
            "role": "security",
            "injected_bugs": ["path traversal in serve_file (../../etc/passwd)",
                              "path traversal in delete_file",
                              "no authentication on either endpoint",
                              "delete can remove arbitrary files",
                              "no input sanitization"],
            "expected_findings": ["path traversal", "no authentication",
                                  "arbitrary file deletion"],
        },
    ),
    Task(
        id="sec-004",
        input=(
            "Audit this webhook handler:\n\n"
            "```python\n"
            "import json\n"
            "import subprocess\n"
            "from flask import Flask, request\n\n"
            "app = Flask(__name__)\n\n"
            "@app.route('/webhook/deploy', methods=['POST'])\n"
            "def deploy_webhook():\n"
            "    data = request.json\n"
            "    branch = data.get('branch', 'main')\n"
            "    repo = data.get('repo', 'myapp')\n"
            "    result = subprocess.run(\n"
            "        f'cd /opt/apps/{repo} && git checkout {branch} && ./deploy.sh',\n"
            "        shell=True, capture_output=True, text=True\n"
            "    )\n"
            "    return {'stdout': result.stdout, 'stderr': result.stderr}\n"
            "```"
        ),
        metadata={
            "role": "security",
            "injected_bugs": ["command injection via branch and repo params",
                              "shell=True with untrusted input",
                              "no webhook signature verification",
                              "exposes stdout/stderr to caller",
                              "no authentication"],
            "expected_findings": ["command injection", "shell=True",
                                  "no webhook verification", "no authentication"],
        },
    ),
    Task(
        id="sec-005",
        input=(
            "Audit this session management:\n\n"
            "```python\n"
            "import uuid\n"
            "import time\n"
            "from flask import Flask, request, jsonify, make_response\n\n"
            "app = Flask(__name__)\n"
            "sessions = {}\n\n"
            "@app.route('/login', methods=['POST'])\n"
            "def login():\n"
            "    # ... auth logic omitted, assume valid ...\n"
            "    session_id = str(uuid.uuid4())\n"
            "    sessions[session_id] = {\n"
            "        'user_id': request.json['user_id'],\n"
            "        'created': time.time()\n"
            "    }\n"
            "    resp = make_response(jsonify({'status': 'ok'}))\n"
            "    resp.set_cookie('session_id', session_id)\n"
            "    return resp\n\n"
            "@app.route('/logout', methods=['POST'])\n"
            "def logout():\n"
            "    session_id = request.cookies.get('session_id')\n"
            "    sessions.pop(session_id, None)\n"
            "    return jsonify({'status': 'logged out'})\n"
            "```"
        ),
        metadata={
            "role": "security",
            "injected_bugs": ["cookie without Secure flag",
                              "cookie without HttpOnly flag",
                              "cookie without SameSite attribute",
                              "no session expiration",
                              "sessions in memory (no persistence)",
                              "no session fixation protection"],
            "expected_findings": ["missing cookie flags",
                                  "no session expiration",
                                  "session fixation"],
        },
    ),
]

# ── CLARIFIER tasks ─────────────────────────────────────────────────
# Tasks with deliberate ambiguities for the clarifier to detect.

CLARIFIER_TASKS = [
    Task(
        id="cla-001",
        input="Build a notification system that alerts users when their balance is low.",
        metadata={"role": "clarifier",
                  "expected_ambiguities": ["low balance threshold", "notification channel",
                                           "which users", "alert frequency"]},
    ),
    Task(
        id="cla-002",
        input="Create a search feature that returns relevant results quickly.",
        metadata={"role": "clarifier",
                  "expected_ambiguities": ["relevant by what criteria", "quickly means what latency",
                                           "search what data", "result format"]},
    ),
    Task(
        id="cla-003",
        input="We need a caching layer for our API to improve performance.",
        metadata={"role": "clarifier",
                  "expected_ambiguities": ["which endpoints", "cache invalidation strategy",
                                           "current latency vs target", "data freshness requirements"]},
    ),
    Task(
        id="cla-004",
        input=(
            "Implement user authentication with social login support. "
            "Must be secure and support all major providers."
        ),
        metadata={"role": "clarifier",
                  "expected_ambiguities": ["all major providers — which ones",
                                           "secure — what threat model",
                                           "existing user base to migrate"]},
    ),
    Task(
        id="cla-005",
        input=(
            "Build a data pipeline that processes customer events in real-time "
            "and stores them for analytics."
        ),
        metadata={"role": "clarifier",
                  "expected_ambiguities": ["real-time — sub-second or minutes",
                                           "event schema", "analytics queries needed",
                                           "data volume", "retention policy"]},
    ),
    Task(
        id="cla-006",
        input="Add rate limiting to prevent abuse of our public API.",
        metadata={"role": "clarifier",
                  "expected_ambiguities": ["rate limits per what — IP, user, API key",
                                           "what counts as abuse",
                                           "response when limited — 429 with retry-after?"]},
    ),
    Task(
        id="cla-007",
        input=(
            "Migrate our monolith to microservices. The app handles user management, "
            "billing, and content delivery."
        ),
        metadata={"role": "clarifier",
                  "expected_ambiguities": ["migration timeline", "which service first",
                                           "shared database during transition",
                                           "zero-downtime requirement"]},
    ),
    # Clear tasks — agent should declare CLEAR
    Task(
        id="cla-008",
        input=(
            "Implement a function that takes a list of integers and returns "
            "the sum of all even numbers. Input: list of ints. Output: single int. "
            "Empty list returns 0. Language: Python."
        ),
        metadata={"role": "clarifier", "expected_status": "CLEAR"},
    ),
    Task(
        id="cla-009",
        input=(
            "Create a REST endpoint POST /api/health that returns HTTP 200 with "
            "JSON body {\"status\": \"ok\", \"timestamp\": \"ISO8601\"}. "
            "No authentication required. Framework: Flask."
        ),
        metadata={"role": "clarifier", "expected_status": "CLEAR"},
    ),
]

# ── TESTER tasks ────────────────────────────────────────────────────
# Code + architecture for the tester to analyze test coverage.

TESTER_TASKS = [
    Task(
        id="tst-001",
        input=(
            "Analyze test coverage for this rate limiter:\n\n"
            "```python\n"
            "# rate_limiter.py\n"
            "import time, threading\n\n"
            "class TokenBucket:\n"
            "    def __init__(self, rate, capacity):\n"
            "        self.rate = rate\n"
            "        self.capacity = capacity\n"
            "        self.tokens = capacity\n"
            "        self.last_refill = time.monotonic()\n"
            "        self.lock = threading.Lock()\n\n"
            "    def consume(self, n=1):\n"
            "        with self.lock:\n"
            "            self._refill()\n"
            "            if self.tokens >= n:\n"
            "                self.tokens -= n\n"
            "                return True\n"
            "            return False\n\n"
            "    def _refill(self):\n"
            "        now = time.monotonic()\n"
            "        elapsed = now - self.last_refill\n"
            "        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)\n"
            "        self.last_refill = now\n"
            "```\n\n"
            "Tests:\n```python\n"
            "def test_basic_consume():\n"
            "    tb = TokenBucket(10, 10)\n"
            "    assert tb.consume() == True\n\n"
            "def test_exceed_capacity():\n"
            "    tb = TokenBucket(1, 2)\n"
            "    assert tb.consume(3) == False\n"
            "```"
        ),
        metadata={"role": "tester",
                  "expected_gaps": ["no concurrency test", "no refill test",
                                    "no boundary test at exactly capacity"]},
    ),
    Task(
        id="tst-002",
        input=(
            "Analyze test coverage for this user registration API:\n\n"
            "Architecture requires: email validation, password hashing, "
            "duplicate detection, welcome email trigger.\n\n"
            "Tests exist for: valid registration, duplicate email 409 response.\n\n"
            "No tests for: password strength validation, email format edge cases, "
            "database failure handling, welcome email failure, concurrent registrations."
        ),
        metadata={"role": "tester",
                  "expected_gaps": ["password validation", "email edge cases",
                                    "db failure", "concurrent registration"]},
    ),
    Task(
        id="tst-003",
        input=(
            "Analyze test coverage for a file upload service:\n\n"
            "Implementation: accepts multipart uploads, validates file type "
            "(allow: jpg, png, pdf), stores to S3, generates thumbnail for images.\n\n"
            "Existing tests: upload jpg returns 200, upload txt returns 400.\n\n"
            "Identify missing test scenarios."
        ),
        metadata={"role": "tester",
                  "expected_gaps": ["zero-byte file", "max size boundary",
                                    "S3 failure", "thumbnail generation failure",
                                    "concurrent uploads same filename"]},
    ),
    Task(
        id="tst-004",
        input=(
            "Analyze test strategy for a payment processing module:\n\n"
            "Components: PaymentGateway (Stripe integration), InvoiceGenerator, "
            "RefundProcessor, WebhookHandler.\n\n"
            "Current tests: unit tests for InvoiceGenerator with mocked gateway.\n\n"
            "What testing strategy and specific tests are needed?"
        ),
        metadata={"role": "tester",
                  "expected_gaps": ["integration test with Stripe sandbox",
                                    "webhook signature verification test",
                                    "refund idempotency", "partial failure handling"]},
    ),
    Task(
        id="tst-005",
        input=(
            "Analyze test coverage for a WebSocket chat server:\n\n"
            "Features: rooms, message history, presence, typing indicators.\n\n"
            "Existing tests: connect/disconnect, send message to room.\n\n"
            "Missing: reconnection, message ordering, room limits, "
            "concurrent typing indicators, history pagination."
        ),
        metadata={"role": "tester",
                  "expected_gaps": ["reconnection with state recovery",
                                    "message ordering under load",
                                    "room capacity limits"]},
    ),
]

# ── DOCUMENTER tasks ────────────────────────────────────────────────
# Projects needing documentation.

DOCUMENTER_TASKS = [
    Task(
        id="doc-001",
        input=(
            "Document this CLI tool:\n\n"
            "Name: stow-dotfiles\n"
            "Purpose: manages dotfiles across machines using symlinks\n"
            "Commands: init, link, unlink, status, diff\n"
            "Config: ~/.stowrc (YAML)\n"
            "Features: machine-specific overrides, encrypted secrets, rollback\n"
            "Stack: Python 3.11+, Click, PyYAML"
        ),
        metadata={"role": "documenter"},
    ),
    Task(
        id="doc-002",
        input=(
            "Document this REST API:\n\n"
            "Service: user-management-api\n"
            "Endpoints: POST /users, GET /users/:id, PATCH /users/:id, "
            "DELETE /users/:id, POST /users/:id/verify-email\n"
            "Auth: Bearer JWT tokens\n"
            "Rate limits: 100 req/min per API key\n"
            "Errors: standard RFC 7807 problem detail format\n"
            "Stack: Go, chi router, PostgreSQL"
        ),
        metadata={"role": "documenter"},
    ),
    Task(
        id="doc-003",
        input=(
            "Document deployment for this microservice:\n\n"
            "Service: billing-processor\n"
            "Runtime: Docker container\n"
            "Dependencies: PostgreSQL, Redis, Stripe API\n"
            "Config: environment variables (12-factor)\n"
            "Health check: GET /health\n"
            "Deployment: Kubernetes with Helm chart\n"
            "Monitoring: Prometheus metrics at /metrics"
        ),
        metadata={"role": "documenter"},
    ),
    Task(
        id="doc-004",
        input=(
            "Document this library:\n\n"
            "Name: retry-kit\n"
            "Purpose: configurable retry with circuit breaker for Python\n"
            "API: RetryExecutor(max_retries, backoff, base_delay), "
            "CircuitBreaker(threshold, timeout), @retry decorator\n"
            "Features: exponential backoff with jitter, composable executors, "
            "state callbacks, async support\n"
            "Install: pip install retry-kit"
        ),
        metadata={"role": "documenter"},
    ),
    Task(
        id="doc-005",
        input=(
            "Document this event-driven system:\n\n"
            "System: order-processing pipeline\n"
            "Events: OrderCreated, PaymentProcessed, OrderShipped, OrderDelivered\n"
            "Components: OrderService, PaymentService, ShippingService, NotificationService\n"
            "Message broker: abstracted (provide examples for both RabbitMQ and Kafka)\n"
            "Error handling: dead letter queue, manual retry UI\n"
            "Monitoring: event throughput, processing latency, DLQ depth"
        ),
        metadata={"role": "documenter"},
    ),
]

# ── DEVOPS tasks ────────────────────────────────────────────────────
# Operational scenarios.

DEVOPS_TASKS = [
    Task(
        id="ops-001",
        input=(
            "Create CI/CD pipeline and deployment for:\n\n"
            "Project: Go monorepo with 5 services and shared libraries\n"
            "Requirements: affected-service detection, parallel builds, "
            "integration tests per service, canary deployment, auto-rollback\n"
            "Environments: staging, production\n"
            "Current: manual deploys via SSH"
        ),
        metadata={"role": "devops"},
    ),
    Task(
        id="ops-002",
        input=(
            "Create operational runbook for:\n\n"
            "Service: real-time bidding platform\n"
            "SLO: 99.9% availability, p99 latency <50ms\n"
            "Components: API gateway, bid engine, campaign store (Redis), "
            "event logger (Kafka), reporting DB (PostgreSQL)\n"
            "Common incidents: Redis OOM, Kafka consumer lag, bid timeout spikes"
        ),
        metadata={"role": "devops"},
    ),
    Task(
        id="ops-003",
        input=(
            "Design monitoring and alerting for:\n\n"
            "System: e-commerce checkout flow\n"
            "Components: cart service, payment gateway, inventory service, "
            "order service, notification service\n"
            "Requirements: detect checkout failures within 1 minute, "
            "payment processing anomalies, inventory sync issues\n"
            "Existing: basic health checks only"
        ),
        metadata={"role": "devops"},
    ),
    Task(
        id="ops-004",
        input=(
            "Create disaster recovery plan for:\n\n"
            "System: multi-region SaaS platform\n"
            "Data stores: PostgreSQL (primary), Redis (cache), S3 (files)\n"
            "RPO: 1 hour, RTO: 4 hours\n"
            "Regions: primary + 1 standby\n"
            "Requirements: automated failover, data consistency verification, "
            "communication plan, regular DR testing"
        ),
        metadata={"role": "devops"},
    ),
    Task(
        id="ops-005",
        input=(
            "Create deployment strategy for database migration:\n\n"
            "Current: PostgreSQL 14, single instance, 500GB data\n"
            "Target: PostgreSQL 16, with read replicas\n"
            "Constraints: maximum 5 minutes downtime, must verify data integrity, "
            "rollback plan if migration fails\n"
            "Application: 3 services depend on this database"
        ),
        metadata={"role": "devops"},
    ),
]

# ── Task corpus registry ─────────────────────────────────────────────

TASK_CORPUS: dict[str, list[Task]] = {
    "architect": ARCHITECT_TASKS,
    "reviewer": REVIEWER_TASKS,
    "developer": DEVELOPER_TASKS,
    "security": SECURITY_TASKS,
    "clarifier": CLARIFIER_TASKS,
    "tester": TESTER_TASKS,
    "documenter": DOCUMENTER_TASKS,
    "devops": DEVOPS_TASKS,
}


def _stable_hash(s: str) -> int:
    """Deterministic hash stable across Python runs."""
    return int(hashlib.md5(s.encode()).hexdigest(), 16)


def get_tasks_for_role(role: str, split: str = "train", limit: int = 10) -> list[Task]:
    """Return tasks for a role, split by stable hash for reproducibility."""
    tasks = TASK_CORPUS.get(role, [])
    if not tasks:
        raise ValueError(
            f"No tasks defined for role: {role}. "
            f"Available: {list(TASK_CORPUS.keys())}"
        )

    if split == "holdout":
        tasks = [t for t in tasks if _stable_hash(t.id) % 5 == 0]
    elif split == "train":
        tasks = [t for t in tasks if _stable_hash(t.id) % 5 != 0]
        # Exclude trap tasks from training — they require alternative scoring
        tasks = [t for t in tasks if t.metadata.get("difficulty") != "trap"]

    return tasks[:limit]
