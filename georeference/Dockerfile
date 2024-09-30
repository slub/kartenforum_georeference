FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.0


# Define an argument for the username
ARG USERNAME
ARG UID

RUN usermod -u 1001 -m -d /home/ubuntu ubuntu \
    && useradd -m -d /home/$USERNAME -u $UID -s /bin/bash $USERNAME \
    && usermod -aG sudo $USERNAME \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers


RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes pipx build-essential python3-dev libvips libvips-tools rsync

USER $USERNAME

ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

RUN pipx install poetry && pipx inject poetry poetry-plugin-bundle

WORKDIR /code

COPY pyproject.toml poetry.lock /code/


# Install dependencies
RUN poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project true \
    && poetry config virtualenvs.options.always-copy true \
    && poetry install --no-interaction --no-ansi

COPY georeference /code/georeference

ENTRYPOINT ["poetry", "run", "fastapi", "run", "georeference/main.py"]