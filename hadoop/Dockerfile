FROM debian:bookworm-slim
ARG HADOOP_VERSION=3.5.0
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    HADOOP_HOME=/opt/hadoop \
    HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop \
    PATH=/opt/hadoop/bin:/opt/hadoop/sbin:$PATH
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jre-headless python3 openssh-server openssh-client wget ca-certificates procps \
    && rm -rf /var/lib/apt/lists/*
RUN wget --show-progress --progress=dot:giga --timeout=60 --tries=3 https://downloads.apache.org/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz \
    && tar -xzf hadoop-${HADOOP_VERSION}.tar.gz -C /opt \
    && mv /opt/hadoop-${HADOOP_VERSION} /opt/hadoop \
    && rm hadoop-${HADOOP_VERSION}.tar.gz \
    && useradd -m -s /bin/bash hadoop \
    && mkdir -p /run/sshd /data/input /data/output /shared-ssh \
    && chown -R hadoop:hadoop /opt/hadoop /data /shared-ssh
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && printf 'export JAVA_HOME=%s\nexport HADOOP_HOME=%s\nexport PATH=$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH\n' "$JAVA_HOME" "$HADOOP_HOME" >> /home/hadoop/.bashrc
EXPOSE 22
ENTRYPOINT ["/entrypoint.sh"]

