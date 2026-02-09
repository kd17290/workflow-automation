FROM python:3.13-slim

RUN echo "Installing System Packages" && \
    apt update && \
    apt-get -y install locales wait-for-it git bash-completion libpq-dev wget curl gcc build-essential python3-dev && \
    pip install --upgrade pip && \
    pip install pipx==1.7.1 && \
    echo "Clean apt cache and unneeded pkgs" && \
    apt-get clean autoclean --yes && \
    apt-get autoremove --yes && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/

# Installing Poetry (Pinning installed version here).
RUN pipx install poetry==2.1.3 pre-commit==3.3.3 && \
    echo "Poetry and pre-commit installed successfully."

# Setting Environment variables for Poetry config settings for virtualenv management.
ENV POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_VIRTUALENVS_CREATE=true

# Ensure the Poetry binary is in the PATH
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /usr/src/app

# Copy pyproject.toml and poetry.lock file for installing dependencies.
COPY pyproject.toml ./

# Install dependencies.
RUN poetry lock
RUN poetry install --no-interaction --no-root --no-ansi --verbose

# Copy remaining source code.
COPY . .

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD curl -f http://localhost:8001/health || exit 1
