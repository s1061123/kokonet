# run:
# docker run -e VPP_CONTROLLER_URL=<vpp controller ip> -e VPP_VTEP_IP=<vpp ip>
FROM alpine:3.5

WORKDIR /app

RUN apk add --update \
	python \
	python-dev \
	py-pip \
	build-base \
  && pip install -r /app/requirements.txt
  && rm -rf /var/cache/apk/*

ONBUILD COPY . /app

EXPOSE 80
CMD ["/usr/bin/gunicorn", "server:app", "--bind", "0.0.0.0:80"]
