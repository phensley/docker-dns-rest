FROM alpine:3.1
MAINTAINER "Patrick Hensley <spaceboy@indirect.com>"
COPY . /data
RUN /data/bootstrap
EXPOSE 80
ENTRYPOINT ["/data/docker_dnsrest"]

