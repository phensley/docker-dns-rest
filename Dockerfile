FROM alpine:3.8
LABEL maintainer="Patrick Hensley <spaceboy@indirect.com>"
COPY . /data
RUN /data/bootstrap
EXPOSE 80
ENTRYPOINT ["/data/docker_dnsrest"]

