# Download base image ubuntu 21.04
FROM ubuntu:21.04

LABEL maintainer="PIKOBYTES GmbH \"[mailto:info@pikobytes.de\]info@pikobytes.de\""

# Define environmental variables
ENV src_dir /opt/kartenforum_georeference
ENV data_dir /opt/kartenforum_georeference/data

RUN apt-get update
RUN DEBIAN_FRONTEND="noninteractive" apt-get install -yq apt-transport-https wget gnupg2 software-properties-common curl vim less python3 python3-virtualenv libpq-dev gdal-bin libgdal-dev postgresql-client rsync

# Copy python files
COPY ./georeference ${src_dir}/georeference
COPY ./setup.py ${src_dir}/

WORKDIR ${src_dir}
VOLUME ${data_dir}

# Set python path
ENV PYTHONPATH "${PYTHONPATH}:${src_dir}"

EXPOSE 6543

# Install service
RUN virtualenv ${src_dir}/python_env
RUN ${src_dir}/python_env/bin/python setup.py install

COPY ./docker/settings.py ${src_dir}/georeference/
COPY ./docker/production.ini ${src_dir}/
COPY ./docker/wait-for-it.sh ${src_dir}/
RUN chmod +x ${src_dir}/wait-for-it.sh
COPY ./docker/startup.sh ${src_dir}/
RUN chmod +x ${src_dir}/startup.sh

#CMD tail -f /dev/null
CMD ["/opt/kartenforum_georeference/startup.sh"]