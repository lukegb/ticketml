import argparse
import ticketml
import serial

BACKENDS = {
    'ibm4610': ticketml.Ibm4610Backend,
    'cbm': ticketml.CbmBackend,
}

parser = argparse.ArgumentParser(description='Print a template.')

parser.add_argument('filenames', metavar='F', type=str, help='templates to print', nargs='+')
parser.add_argument('--backend', dest='backend', type=str, help='Printer backend', required=True, choices=BACKENDS.keys())
parser.add_argument('--serial', dest='serial_port', type=str, help='Serial port location', required=True)
parser.add_argument('--baudrate', dest='baudrate', type=int, help='Serial port baudrate', required=True)

args = parser.parse_args()

serial_port = serial.Serial(args.serial_port, args.baudrate)
backend = BACKENDS.get(args.backend)(serial_port)

for filename in args.filenames:
    with open(filename, 'r') as f:
        ticket_xml = f.read()
    ticket_xml = ''.join([x.lstrip() for x in ticket_xml.split('\n')])
    ticket = ticketml.TicketML.parse(ticket_xml)
    ticket.go({}, backend)
