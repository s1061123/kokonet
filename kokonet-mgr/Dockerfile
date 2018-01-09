# run:
# docker run -e VPP_CONTROLLER_URL=<vpp controller ip> -e VPP_VTEP_IP=<vpp ip>
FROM alpine:3.6

WORKDIR /app
#ONBUILD COPY . /app
COPY . /app

RUN apk add --update \
	python \
	python-dev \
	py-pip \
	build-base \
  && pip install --upgrade pip \
  && pip install -r /app/requirements.txt \
  && rm -rf /var/cache/apk/*


EXPOSE 80
CMD ["/usr/bin/gunicorn", "--log-file", "-", "--bind", "0.0.0.0:80", "server:app"]
