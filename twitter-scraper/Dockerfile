# Twitter Scraper - powered by Agent-Reach (https://github.com/Panniantong/Agent-Reach)
#
# Agent-Reach is the "give your AI agent eyes on the internet" project. It
# health-checks and routes to upstream platform tools; for Twitter/X its
# selected server backend is twitter-cli. Install that backend directly so a
# failed check for an unrelated optional Agent-Reach channel cannot fail this
# image build.
#
# NOTE: the real project lives at github.com/Panniantong/agent-reach and is
# NOT the "agent-reach" package on PyPI (that's an unrelated project) - it
# must be installed from the GitHub archive, per Agent-Reach's own install
# docs (docs/install.md).
FROM python:3.12-slim

WORKDIR /app

# git: pipx needs it to install from a GitHub archive/VCS URL.
# curl/ca-certificates: Agent-Reach's own dependencies (Jina Reader reads, etc).
RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip pipx
ENV PATH="/root/.local/bin:${PATH}"
RUN pipx ensurepath

# Install Agent-Reach from its GitHub source (not PyPI - see note above).
RUN pipx install https://github.com/Panniantong/agent-reach/archive/main.zip

# Agent-Reach's documented Twitter backend. Pin it in the scraper's Python
# environment because the local compatibility wrapper imports twitter-cli
# internals before delegating to its command entrypoint.
RUN pip install --no-cache-dir "twitter-cli==0.8.5"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scraper.py twitter_cli_runner.py ./

ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=5m --timeout=15s --start-period=1m --retries=2 \
    CMD twitter --version >/dev/null 2>&1 && python -u scraper.py --healthcheck

CMD ["python", "-u", "scraper.py"]
