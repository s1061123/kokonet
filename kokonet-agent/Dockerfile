# run:
# docker run -e DATAPLANE_IP=<this node ip> -e ETCD_CLIENT_HOST=<etcd host> -e ETCD_CLIENT_PORT=<port>
FROM alpine:3.6

WORKDIR /app
COPY . /app

RUN apk add --update \
	python \
	python-dev \
	py-pip \
	build-base \
	wget \
  && pip install --upgrade pip \
  && pip install -r /app/requirements.txt \
  && wget --no-check-certificate https://github.com/redhat-nfvpe/koro/releases/download/v0.1/koro_v0.1_linux_amd64.tar.gz \
  && tar xvfpz koro_v0.1_linux_amd64.tar.gz \
  && cp koro_v0.1_linux_amd64/koro . \
  && rm -rf /var/cache/apk/*

ENTRYPOINT ["/app/agent.py"]
