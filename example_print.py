import argparse
import ticketml
import serial

BACKENDS = {
    'ibm4610': ticketml.Ibm4610Backend,
    'cbm': ticketml.CbmBackend,
}

class MockSerial(object):
    def write(self, data):
        print ">>> {}".format(data.encode('hex'))

    def flush(self):
        print "> FLUSH"


parser = argparse.ArgumentParser(description='Print a template.')

parser.add_argument('filenames', metavar='F', type=str, help='templates to print', nargs='+')
parser.add_argument('--backend', dest='backend', type=str, help='Printer backend', required=True, choices=BACKENDS.keys())
output_group = parser.add_mutually_exclusive_group(required=True)
output_group.add_argument('--debug', action='store_true')
output_group.add_argument('--serial', dest='serial_port', type=str, help='Serial port location')
parser.add_argument('--baudrate', dest='baudrate', type=int, help='Serial port baudrate', default=19200)

args = parser.parse_args()

if args.serial_port:
    output = serial.Serial(args.serial_port, args.baudrate)
elif args.debug:
    output = MockSerial()
backend = BACKENDS.get(args.backend)(output)

for filename in args.filenames:
    with open(filename, 'r') as f:
        ticket_xml = f.read()
    ticket_xml = ''.join([x.lstrip() for x in ticket_xml.split('\n')])
    ticket = ticketml.TicketML.parse(ticket_xml)
    ticket.go({}, backend)
