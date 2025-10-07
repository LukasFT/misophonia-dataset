# Note: This Dockerfile mixes the base and dev dependencies for convenience. Split it for production use.
FROM docker.io/nvidia/cuda:12.0.0-base-ubuntu22.04

# Arguments
# * User ID of the user 'app'
ARG USER_UID=1000
# * Group ID of the user 'app'
ARG USER_GID=1000

# Install OS dependencies
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV TZ=Etc/UTC
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    # Configure localization
    && apt-get install -y --no-install-recommends tzdata \
    && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    # Install dependencies
    && apt-get install -y \
      # * Build:
      curl \
      # Needed for R:
      ca-certificates \
      gnupg \
      wget \
      build-essential \
      # * Dev:
      git \
      bash \
      fish \
    # * Remove apt cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Install R packages (using r2u, see https://github.com/eddelbuettel/r2u)
RUN \
    # Fetch key
    wget -q -O- https://eddelbuettel.github.io/r2u/assets/dirk_eddelbuettel_key.asc \
      | tee -a /etc/apt/trusted.gpg.d/cranapt_key.asc \
    # Add the apt repo
    && echo "deb [arch=amd64] https://r2u.stat.illinois.edu/ubuntu jammy main" > /etc/apt/sources.list.d/cranapt.list \
    && apt-get update -qq \
    # Ensure you have current R binaries
    && wget -q -O- https://cloud.r-project.org/bin/linux/ubuntu/marutter_pubkey.asc \
      | tee -a /etc/apt/trusted.gpg.d/cran_ubuntu_key.asc \
    && echo "deb [arch=amd64] https://cloud.r-project.org/bin/linux/ubuntu jammy-cran40/" \
        > /etc/apt/sources.list.d/cran_r.list \
    && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys \
        67C2D66C4B1D4339 51716619E084DAB9 \
    && apt-get update -qq \
    && apt-get install --yes --no-install-recommends r-base-dev \
    # Use pinning for the r2u repo
    && echo "Package: *" > /etc/apt/preferences.d/99cranapt \
    && echo "Pin: release o=CRAN-Apt Project" >> /etc/apt/preferences.d/99cranapt \
    && echo "Pin: release l=CRAN-Apt Packages" >> /etc/apt/preferences.d/99cranapt \
    && echo "Pin-Priority: 700"  >> /etc/apt/preferences.d/99cranapt \
    # Install r-cran- packages
    && apt-get install --yes \
      r-cran-lme4 \
      r-cran-lmertest \
      r-cran-emmeans \
    # Verify installation
    && Rscript -e 'print(R.version.string); library(lme4); library(lmerTest); library(emmeans); sessionInfo()' \
    # Remove apt cache to reduce image size
    && rm -rf /var/lib/apt/lists/*



# Create a non-root user called app and switch to it
RUN groupadd -g $USER_GID app && useradd -u $USER_UID -g $USER_GID -m app
USER app
ENV PATH="/home/app/.local/bin:${PATH}"

# * Install uv (dependency of management)
# ** See https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
# ** See https://github.com/astral-sh/uv-docker-example/blob/main/Dockerfile
# USER root
# # * Download the latest installer
# ADD https://astral.sh/uv/install.sh /uv-installer.sh
# # * Run the installer then remove it
# RUN sh /uv-installer.sh && rm /uv-installer.sh
# USER app
COPY --from=ghcr.io/astral-sh/uv:0.5.24 /uv /uvx /bin/

# Install the project into `/build`
WORKDIR /build

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# # Copy from the cache instead of linking since it's a mounted volume
# ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
COPY .python-version .python-version
RUN uv python install
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project
# Place executables in the environment at the front of the path
ENV UV_PROJECT_ENVIRONMENT="/build/.venv"
ENV PATH="/build/.venv/bin:$PATH"

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
WORKDIR /app
ADD . /app
