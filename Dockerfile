# Copy into each app's repo as `Dockerfile`, changing only the module name on
# the last line. Image tag should match the app's .python-version.

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# Dependencies first, so editing your own code does not reinstall Django.
# --locked fails loudly if uv.lock disagrees with pyproject.toml, which is what
# you want on a server: install what you tested, or stop.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --group prod

COPY . .

# Runs at build time, against the SQLite default — no database is reachable
# here, and collectstatic does not need one. Needs STATIC_ROOT in settings.py
# (see settings-snippet.py); WhiteNoise serves the result at runtime.
#
# collectstatic loads settings.py, so every env("...") without a default must
# have a value here. Compose's `environment:` and the server's .env only apply
# when the container runs, not while the image builds, and the app's own .env
# is gitignored. The placeholder is never connected to and does not persist
# into the running container, where Compose supplies the real REDIS_URL.
RUN REDIS_URL=redis://build-placeholder:6379 python manage.py collectstatic --noinput

# migrate on start is safe to repeat and keeps deploys to one command. Each app
# owns its own database, so there is no cross-app migration race.
# 1 worker + threads, not 4 workers: on a 1 GB box, threads are nearly free and
# processes are not.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec daphne -b 0.0.0.0 -p 8000 locallibrary_config.asgi:application"]

# For the Channels app, swap the last line for:
# CMD ["sh", "-c", "python manage.py migrate --noinput && exec daphne -b 0.0.0.0 -p 8000 locallibrary_config.asgi:application"]
