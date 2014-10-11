
docker-dns-rest
---------------

A RESTful DNS service for Docker containers.

This service is used to cover a specific use cases for testing applications
which rely on DNS for service discovery, and come bundled with configurations
for certain environments.  

For example, to fool a service into thinking its running in a staging
environment, we can create several named containers and map a series of domain
names to them.  When the containers come online, the dnsrest service maps the
domain names to ip addresses and answers DNS queries from the other containers.

This enables us to make an application believe it is running inside a given
environment, which uses hard-coded DNS entries.


