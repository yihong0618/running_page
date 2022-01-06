#!/usr/bin/env python
#coding:utf-8
# Author:  mozman --<mozman@gmx.at>
# Purpose: pattern module
# Created: 27.09.2010
# Copyright (C) 2010, Manfred Moitzi
# License: MIT License

import re

#coordinate ::= number ("em" | "ex" | "px" | "in" | "cm" | "mm" | "pt" | "pc" | "%")?
coordinate = re.compile(r"(^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)(cm|em|ex|in|mm|pc|pt|px|%)?$")

#length ::= number ("em" | "ex" | "px" | "in" | "cm" | "mm" | "pt" | "pc" | "%")?
length = coordinate

#angle ::= number (~"deg" | ~"grad" | ~"rad")?
angle = re.compile(r"(^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)(deg|rad|grad)?$")

# numbers without units
number = re.compile(r"(^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)$")

# number as percentage value '###%'
percentage = re.compile(r"(^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)%$")

#frequency ::= number (~"Hz" | ~"kHz")
frequency = re.compile(r"(^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)(Hz|kHz)?$")

#time ::= number (~"s" | ~"ms")
time = re.compile(r"(^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)(s|ms)?$")
