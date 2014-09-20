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
