## Configuration infrastructure for RUNC network and hosts

This is a collection of scripts which eases life of a system administrator.
There is a single configuration file for all managed machines and a number
of utilities which generate uniform settings for many services, including:

- **Networking** (DHCP, forward and reverse DNS, iptables port forwarding
  and access rules, Nginx reverse proxy etc);
- **Monitoring** (generate Nagios config based on all declared hosts and
  services);
- **Computation services** (SLURM configs and distcc machine hosts are
  dynamically generated with proper machine resources declaration, allowing
  to exploit all available computing power);
- **SSH known hosts** for secure access (all machines automatically and
  securely explore each other public keys without any administrator
  intervention and generate single shell script which manages keys
  for all hosts);
- **Centralised configuration** of managed hosts. Puppet is heavily used
  and manifests are derived from templates and main configuration file.
  This ensures consistent system configuration on a number of hosts;
- various useful **utilities**, e.g. quickly wake up a host with Wake-on-LAN
  by
  host name or alias, or build a network map using information from config
  file and ARP tables on network devices.


### Project structure

The structure of the project is as follows:

- [`cfg/`](cfg/): this is the directory with the main config file
  ([`conf.yaml`](cfg/conf.yaml)) and various templates for other files.
  Templates are written using [Jinja2](http://jinja.pocoo.org/docs/dev/)
  templating language. The main configuration file uses very convenient
  and concise [YAML](http://www.yaml.org/) syntax;
- [`nagios/`](nagios/): this is where some files useful for [Nagios]
  (http://www.nagios.org/) reside;
- [`parse/`](parse/): this directory contains Python code for parsing and
  validating the main config file and other auxiliary files;
- [`gen/`](gen/): this directory contains Python code for generating a lot
  of things (config files, scripts etc.) using templates and the state
  parsed from the main config file;
- [`puppet/`](puppet/): this directory contains [Puppet]
  (http://puppetlabs.com/puppet/what-is-puppet) modules and other
  Puppet-specific stuff.
- [`util/`](util/): some useful stuff which does not belong to cathegories
  listed above resides here, mainly there are a bunch of Bash scripts.

There are two entry points. [`Main.py`](main.py) is a Python script for
executing a generation process which only operates with templates and other
text stuff and does not touch the system in any way. On the other hand
there is [`do.sh`](do.sh) Bash script which is a wrapper for `main.py` and
does actual work generating configuration of various services and takes
care of reload/restart signaling when it is necessary. It contains a number
of shell functions which may be used separately or in batch mode. Every
function in this file does some piece of configuration in such a way that
a service is touched only if it is necessary. This enables the following
scenario for the administrator: edit `conf.yaml`, check, commit, then
simply execute `do.sh` and it will automatically apply all relevant changes.


### The main configuration file

The main configuration file ([`conf.yaml`](cfg/conf.yaml)) consists of a
  number of *sections*, each of which represents a list of entities of some
  kind:
- **People**. This is a list of nicknames along with their associated contact
  information, useful for e-mail notifications from monitoring, automatic
  updates and other services.
- **Defaults**. This section contanins a bunch of default values for other
  sections, such as default monitoring host IP address or default network
  prefix in host descriptions (which may be omitted to avoid duplication).
- **Networks**. This is a list of IPv4 (and, in future, maybe IPv6) networks
  known to the system. Each network may have some attributes, e.g. `rdns`
  means that we should build reverse DNS zone for this network, while `dhcp`
  defines a range of IP addresses that should be used by DHCP server for
  dynamic IP address pool and so on.
- **Groups**. Groups define properties common for a number of hosts to avoid
  duplication and provide more structure. Their second purpose is to add some
  grouping for hosts to services that support grouping functionality natively
  (for example, Nagios or SLURM). Every group has unique name, may contain a
  list of hosts (which are defined using Python regular expression syntax)
  or other groups, and may define a list of *properties* which should apply to
  all contained entities.
- **Hosts**. The rest of main config file is a long list of hosts known to
  the system. Each host has a host name as the only required attribute, which
  goes first in it's description. It may have some shorter names called
  *aliases*, which help to identify it with one or two letters in many places.
  Host may have an IP address, a number of MAC addresses associated with it,
  and a dictionary of *properties*. Host properties define some host-specific
  data, for example who admins that host (see **People** above), which services
  this host has, what UDP ports sholud be forwarded to that host or what UPS
  powers it. Propertes may have arbitrary structure convenient for specific
  purpose (for example, running services are most naturally expressed as a
  list). The names and semantics of properties are defined by templates and
  generation code which uses them. Unsupported properties are quietly skipped.

As the main config file is read and written entirely by humans, there are two
main thoughts which constitute it's philosophy:
* All terms should be self-descripting. If someone sees something which looks
  like MAC address, that should be so. And if there is `https` in some place,
  you should't have to look through the documentation to find out what it is.
* Duplication should be avoided as much as possible. Less duplication means
  less code to read and, consequently, less errors. Group functionality,
  although somewhat odd and complicated, was specifically developed for this
  purpose. Also there are host aliases, default network prefixes, regular
  expressions and generally beautiful and clean YAML markup which all serve
  this purpose.
