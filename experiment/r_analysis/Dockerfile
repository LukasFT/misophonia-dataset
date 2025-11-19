# Simple, stable R base image
FROM rocker/r-ver:4.4.1

# Arguments
# * User ID of the user 'app'
ARG USER_UID=1000
# * Group ID of the user 'app'
ARG USER_GID=1000

ARG DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV TZ=Etc/UTC

RUN apt-get update \
    # Configure localization
    && apt-get install -y --no-install-recommends tzdata \
    && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    # Install dependencies
    && apt-get install -y \
      # * Build:
      cmake \
      libicu-dev \
    # * Remove apt cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g $USER_GID app && useradd -u $USER_UID -g $USER_GID -m app
USER app
ENV PATH="/home/app/.local/bin:${PATH}"


# put renv's stuff under /build
ENV RENV_CONFIG_REPOS_OVERRIDE=https://packagemanager.posit.co/cran/__linux__/jammy/latest
ENV RENV_CONFIG_USE_CACHE=TRUE
ENV RENV_CONFIG_CACHE_SYMLINK=TRUE
ENV RENV_CONFIG_CACHE_DIR=/home/app/.local/share/renv/cache/v4/R


USER root
# Install packages (I did not want to bother with renv because I want to mount /app)
RUN R -q -e 'install.packages("remotes", repos=Sys.getenv("RENV_CONFIG_REPOS_OVERRIDE"))' \
 && R -q -e 'remotes::install_version("lme4",      version = "1.1-37", repos = Sys.getenv("RENV_CONFIG_REPOS_OVERRIDE"))' \
 && R -q -e 'remotes::install_version("lmerTest",  version = "3.1-3",    repos = Sys.getenv("RENV_CONFIG_REPOS_OVERRIDE"))' \
 && R -q -e 'remotes::install_version("emmeans",   version = "1.11.2-8",   repos = Sys.getenv("RENV_CONFIG_REPOS_OVERRIDE"))'

USER app

WORKDIR /app
COPY . .

CMD ["Rscript", "analysis.R"]
