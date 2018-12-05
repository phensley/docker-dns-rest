
docker-dns-rest
---------------

A RESTful DNS service for Docker containers.

This service is used to cover a specific use cases for testing applications
which rely on DNS for service discovery, and come bundled with configurations
for certain environments.  

For example, to fool a service into thinking its running in a staging
environment, we can create several named containers and map one or more domain
names to them.  When the containers come online, the dnsrest service maps the
domain names to the container IP addresses and answers DNS queries from the
other containers.

Usage
-----


First, start docker-dns-rest container. The docker-dns-rest container listens
on port 80 by default, so depending on how you run Docker you may need to map
a host port:

    % docker run -d -p 5080:80 -v /var/run/docker.sock:/docker.sock --name dns \
        phensley/docker-dns-rest --verbose 

Tail the logs:

    % docker logs -f dns

Ensure you have routing from your local machine to the `docker-dns-rest`
container.   Assuming you're running Docker under a Vagrant VM on the local
host, add a route to the VM's IP (`192.168.222.5` in this example):

    % route add -net 172.17.0.0 192.168.222.5

Get the IP of the DNS container:

    % docker inspect -f '{{.NetworkSettings.IPAddress}}' dns
    172.17.0.2

The previous command will fail if a user defined network is present. In this case use:

    % docker inspect -f '{{.NetworkSettings.Networks.yournetwork.IPAddress}}' dns
    172.17.0.2

Next, add some names to the DNS registry.  We can associate one or more names
with a container by `id` or `name`.  We'll associate some domain names with
the container name `www`:

    % curl -X PUT -H 'Content-Type: application/json' \
        -d '{"domains": ["*.example.com", "www.staging.internal.com"]}' \
        http://172.17.0.2:80/container/name/www
    {"code": 0}

Now, start up a container with that name:

    % docker run -it --name www ubuntu bash
    root@db8fabbaf1d6:/#
    
You should see some output in the DNS log:

    192.168.222.1 - - [2014-10-11 15:25:34] "PUT /container/name/www HTTP/1.1" 200 134 0.000366
    2014-10-11T15:26:29.198673 [dnsrest] setting www (83854cf229) as active
    2014-10-11T15:26:29.198821 [dnsrest] added *.example.com. -> 172.17.0.3
    2014-10-11T15:26:29.198900 [dnsrest] added www.staging.internal.com. -> 172.17.0.3

Confirm the `www` container's IP address:

    % docker inspect -f '{{.NetworkSettings.IPAddress}}' www
    172.17.0.3


Now you can query some names against the DNS server:

    % host test.example.com 172.17.0.2
    Using domain server:
    Name: 172.17.0.2
    Address: 172.17.0.2#53
    Aliases:

    test.example.com has address 172.17.0.3
    test.example.com has address 172.17.0.3

When you stop the `www` container, the names will be unregistered:

    % docker stop www

    ... dns logs ...
    2014-10-11T15:28:35.050232 [dnsrest] setting www (83854cf229) as inactive
    2014-10-11T15:28:35.050378 [dnsrest] removed *.example.com. -> 172.17.0.3
    2014-10-11T15:28:35.050462 [dnsrest] removed www.staging.internal.com. -> 172.17.0.3

Now start the `www` container again and the names will be registered again under the new IP address:

    % docker start www

    ... dns logs ...
    2014-10-11T15:29:37.374072 [dnsrest] setting www (83854cf229) as active
    2014-10-11T15:29:37.374209 [dnsrest] added *.example.com. -> 172.17.0.4
    2014-10-11T15:29:37.374286 [dnsrest] added www.staging.internal.com. -> 172.17.0.4

    ... confirm the ip is correct ...
    % docker inspect -f '{{.NetworkSettings.IPAddress}}' www
    172.17.0.4

You can use the DNS server from your containers using:

    % docker run -it --name shell --dns 172.17.0.2 --dns-search example.com ubuntu bash
    root@e776fff8d971:/# ping foo
    PING foo.example.com (172.17.0.4) 56(84) bytes of data.
    64 bytes from 172.17.0.4: icmp_seq=1 ttl=64 time=0.087 ms
    64 bytes from 172.17.0.4: icmp_seq=2 ttl=64 time=0.102 ms
    64 bytes from 172.17.0.4: icmp_seq=3 ttl=64 time=0.106 ms   
    ^C

    root@e776fff8d971:/# ping www.staging.internal.com
    PING www.staging.internal.com (172.17.0.57) 56(84) bytes of data.
    64 bytes from 172.17.0.4: icmp_seq=1 ttl=64 time=0.056 ms
    64 bytes from 172.17.0.4: icmp_seq=2 ttl=64 time=0.106 ms
    ^C

    ... dns logs ...
    2014-10-11T15:32:54.874238 [dnsrest] resolved foo.example.com. -> 172.17.0.4
    2014-10-11T15:36:40.487780 [dnsrest] resolved www.staging.internal.com. -> 172.17.0.4

The DNS server will also forward any names which do not match, to the resolver you specify (default is `8.8.8.8`). This can be disabled by setting the `--no-recursion` command line option:
    
    root@e776fff8d971:/# ping github.com
    PING github.com (192.30.252.130) 56(84) bytes of data.
    64 bytes from 192.30.252.130: icmp_seq=1 ttl=61 time=33.4 ms
    64 bytes from 192.30.252.130: icmp_seq=2 ttl=61 time=31.8 ms


