
""" Generates the CollectD JMX configuration for Storm worker nodes
    based off of values pulled from the cluster's Ambari instance"""
import re
import subprocess
from string import Template
from optparse import OptionParser

CONNECTION_TEMPLATE = Template("""
<Connection>
  Host "$host_name"
  ServiceURL "service:jmx:rmi:///jndi/rmi://$service_host/jmxrmi"
  InstancePrefix "$instance"
  Collect "memory-heap"
</Connection>
""")


def get_supervisor_slots():
    proc = subprocess.Popen(['storm', 'remoteconfvalue',
                             'supervisor.slots.ports'], stdout=subprocess.PIPE)
    line = next(iter(proc.stdout or []), None)
    return parse_slots(line)


def parse_slots(config_line):
    # Expects output as "supervisor.slots.ports: [6700 6701 ...]"
    return re.search(r"\[([0-9 ]+)\]", config_line).group(1).split(" ")


def create_connection_block(slot):
    return CONNECTION_TEMPLATE.substitute(host_name='localhost-{}'.format(slot),
                                          service_host='localhost:{}'.format(
                                              slot),
                                          instance='worker-{}'.format(slot))


def get_worker_jmx_template(path_string):
    template_text = open(path_string)
    return Template(template_text.read())


def generate_worker_config():
    parser = OptionParser()
    parser.add_option("-t", "--template", dest="template", default="templates/worker_jmx.conf",
                      help="Template file location")

    parser.add_option("-o", "--output", dest="output",
                      default="worker/collectd_oms_worker_jmx.conf", help="Output File")

    (options, _) = parser.parse_args()

    slots = get_supervisor_slots()
    worker_connections = ""
    for slot in slots:
        worker_connections += create_connection_block(slot)

    print 'Created worker blocks for slots {}'.format(slots)

    jmx_template = get_worker_jmx_template(options.template)
    open(options.output, 'w').write(jmx_template.substitute(
        worker_connections=worker_connections))


if __name__ == '__main__':
    generate_worker_config()
