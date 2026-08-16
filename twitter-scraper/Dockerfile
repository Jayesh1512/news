# Twitter Scraper - powered by Agent-Reach (https://github.com/Panniantong/Agent-Reach)
#
# Agent-Reach is the "give your AI agent eyes on the internet" project. It
# installs, health-checks, and routes to upstream platform tools; for
# Twitter/X it selects twitter-cli. We install Agent-Reach itself and run
# its own installer (`agent-reach install --channels=twitter`) so the
# container tracks upstream's chosen backend instead of hardcoding one.
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

# Run Agent-Reach's own installer, scoped to just the twitter channel. This
# provisions twitter-cli (its currently-selected Twitter backend) the same
# way Agent-Reach would set it up for any AI agent.
RUN agent-reach install --env=server --system --channels=twitter

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scraper.py .

ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=5m --timeout=15s --start-period=1m --retries=2 \
    CMD twitter --version >/dev/null 2>&1 && python -u scraper.py --healthcheck

CMD ["python", "-u", "scraper.py"]
