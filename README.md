# ticketml [![Build Status](https://travis-ci.org/lukegb/ticketml.svg?branch=master)](https://travis-ci.org/lukegb/ticketml) [![PyPI Version](https://pypip.in/version/ticketml/badge.svg?style=flat)](https://pypi.python.org/pypi/ticketml)
A small XML-based markup language for tickets

Why?
====

As part of the code I write for [Imperial Cinema](http://www.imperialcinema.co.uk), I decided
I need some way of cleanly abstracting over multiple different (but similar) ticket printers.

I decided on a sort-of HTML-ish language, for which you will find a parser and ticket printing
backend for the following receipt printers:

* Citizen CBM-1000
* IBM 4610 family (tested on the 4610-TF6)

The XML
=======

The XML document has the following sort of style:

```xml
<?xml version="1.0" ?>
<ticket>
  <head>
    <logo num="1" />
    not bold<b> suddenly bold</b> not bold again<br />
    not underlined <u>suddenly underlined</u> not underlined<br />
    now <b>for <u>a mix</u></b> <u>of <b>settings</b></u><br/>
    <align mode="center"><logo num="2" /></align>
    base font<br />
    <font width="2">2x wide</font><br />
    <font height="2">2x high</font><br />
    <font width="2" height="2">2x big</font><br />
    <font width="8" height="8">MASSIVE</font>
  </head>
</ticket>
```

(Note that this document is formatted neatly - leading per-line whitespace is NOT stripped by the parser and may cause you issues!)

The following tags are implemented - unknown tags are ignored (but are still recursed into!):

* `ticket`: this is the root tag and is not treated specially
* `b`: activates emphasis (usually bold)
* `u`: activates underlining
* `logo num="NUMBER"`: prints pre-loaded image NUMBER
* `align mode="left|right|center"`: changes the alignment of text
* `br`: prints a newline
* `font (width="WIDTH") (height="HEIGHT")`: changes the font width/height multiplier

Using it
========

At the moment there's a fairly simplistic API. In order to get started, you'll need some sort of file-like output device. This is usually a PySerial `Serial` object.

```python
import serial
output = serial.Serial('/dev/ttyS1', 19200)
```

Now that you have an output device, you can construct a `Backend`. At present there's a choice of two, the `CbmBackend` (for Citizen CBM-1000 printers) and the `Ibm4610Backend` (for IBM 4610 series printers). Backends are up to take whatever arguments they choose - at the moment this is just the output device they should talk to.

```python
backend = ticketml.Ibm4610Backend(output)
```

Now you can finally construct a parser. This takes place in two stages - first you parse the input XML, then you tell the parser to render it to the output device:

```python
ticket = ticketml.TicketML.parse('<?xml version="1.0" ?>\n<ticket>Hello! This is my first ticket!</ticket>')
context = {}
ticket.go(context, backend)
```

The `context` parameter is unused at the moment, but is planned to be used for future templating functionality.
