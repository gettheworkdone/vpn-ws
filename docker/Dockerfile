FROM debian:bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential make gcc libssl-dev nginx apache2-utils openssl python3 python3-pip gettext-base \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN make clean && make
RUN pip3 install --no-cache-dir flask gunicorn

RUN htpasswd -bc /etc/nginx/.htpasswd cucumber potato
RUN mkdir -p /etc/nginx/templates /data/certs
COPY docker/nginx.conf.template /etc/nginx/templates/lollipop.conf.template
COPY docker/entrypoint.sh /entrypoint.sh

EXPOSE 80 443
CMD ["/entrypoint.sh"]
