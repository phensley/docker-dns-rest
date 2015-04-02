FROM alpine:3.1
MAINTAINER "Patrick Hensley <spaceboy@indirect.com>"
COPY . /data
RUN /data/bootstrap
ENTRYPOINT ["/data/docker_dnsrest"]

