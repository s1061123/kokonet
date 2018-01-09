# run example:
# docker run -d -p 5000:5000 --name kokonet-vpp --privileged -v /run/vpp:/run/vpp <image>
#FROM centos/tools:latest
FROM centos:centos7

WORKDIR /app
COPY . /app
COPY fdio-release.repo /etc/yum.repos.d/
COPY supervisord.conf /etc/supervisord.conf

#RUN yum check-update ca-certificates
RUN yum -y update \
  && yum -y install iproute numactl \
  && yum -y install epel-release \
  && yum -y install vpp vpp-api-python vpp-plugins supervisor python-pip \
  && pip install --upgrade pip \
  && pip install flask gunicorn ipaddress cffi

ENTRYPOINT ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
#ENTRYPOINT ["/usr/bin/gunicorn", "server:app", "--bind", "0.0.0.0:5000"]
