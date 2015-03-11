# ticketml
A small XML-based markup language for tickets

As part of the code I write for [Imperial Cinema](http://www.imperialcinema.co.uk), I decided
I need some way of cleanly abstracting over multiple different (but similar) ticket printers.

I decided on a sort-of HTML-ish language, for which you will find a parser and ticket printing
backend for the following receipt printers:

* Citizen CBM-1000
* IBM 4610 family (tested on the 4610-TF6)

The XML document has the following sort of style:

```
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
