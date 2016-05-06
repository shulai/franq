===========
Franq Guide
===========

About Franq
===========

Franq is a full featured PyQt4 based reporting engine. It provides all the
features commonly found in other reporting tools. Franq is compatible with
Python 2.7 and 3.2+.

Why Franq?
==========

Franq makes a good match for Python PyQt-based desktop applications:

* Python 2/3 support.
* No extra requirements besides PyQt4.
* Trivial output to screen, printer and PDF files.
* Rich feature set.
* Supports several coding styles.
* Actively supported

Please note that being PyQt based doesn't exclude using it in console, web or
other type of applications, as far Qt/PyQt are available in your system.

Anatomy of a Franq report
=========================

Every report definition is composed of rectangular zones called bands. Each
band have smaller zones of text or graphics called elements. Each
element represents a value of your data.

The combination of a report definition and the data sets provided at render
time makes the output of the report.

A report can have:

* A begin band: Printed at the begining of the report.
* A summary band: Printed at the end of the report.
* A header band: Printed at the top of each page. Optionally can be skipped in the
  first page, so the begin band appears at the top.
* A footer band: Printed at the bottom of each page. Optionally can be skipped in
  the last page, so the summary band close the report.
* Detail bands: Each prints once per each object in the associated data set.
  A detail band is special as it makes the current item of its data set change
  every time it is printed, unlike regular bands that just peek the data item.
  A report can have several detail bands.
* Sections: Detail bands live inside sections. Sections are parts of the report
  that can have different properties.

Sections currently can have different number of columns and different column
spacing. In a future can have different page sizes and/or orientation. Each
section can include one or more detail bands.

Each band in turn can have a child band. Child bands allows content related
to the parent band to be printed in a separate page if necessary.

Also, each detail band also can have:

* A begin band: Printed at the begining of the detail.
* A header band: Printed at the begining of the detail after the begin band,
  and in each new column or page.
* A footer band: Printed at the end of each column or page, and at the end of
  the detail.
* A summary band: Printed after the end of the detail.
* Groups, each with optional header and footer bands. Groups can be nested.
* Subdetails: For each item in the dataset, a sequence from an item attribute
  can be rendered as a subdetail. Subdetails can also be nested.

Each Band can have a number of diferent elements:

* Label: A static text.
* Field: An attribute from the data item
* Function: The text resulting from evaluating a function on the item
* Line: Draws a line.
* Box: Draws a box.
* Image: Renders an image from a file or from a QPixmap object.

First steps
===========

The minimal possible example code is an empty report::

	import sip
	sip.setapi("QString", 2)

	from PyQt4 import QtGui
	from franq import Report


	class EmptyReport(Report):
	    pass

	app = QtGui.QApplication([])

	r = EmptyReport()

	printer = QtGui.QPrinter()
	printer.setOutputFileName('empty.pdf')
	r.render(printer)


While not very interesting, it is a valid skeleton to work upon. The
only remarkable detail is using the class Report as the base class
for our empty report.

For a slightly more interesting example, replace the EmptyReport
class with the next one::

	from franq import Report, Band, Label, mm


	class BeginBandReport(Report):

	    background = QtGui.QBrush(QtGui.QColor("cyan"))
	    begin = Band(
		border=QtGui.QColor("blue"),
		background=QtGui.QBrush(QtGui.QColor("white")),
		elements=[
		    Label(top=5 * mm, left=5 * mm, height=5 * mm, width=30 * mm,
		        text=u"Hello World")
		    ])

This example introduces several concepts:

1. The attribute ``background`` of the report is set. Note that all
   graphic properties in Franq are defined using standard PyQt
   objects.
2. The ``begin`` band is defined as an instance of the Band class. Band
   properties are set as constructor parameters.
3. A label element is created, being a Label object defined into the
   elements attribute of the Band object. elements is always a sequence
   of Element objects.
4. Measures are in millimeters, using the ``mm`` constant. Other units
   available are ``cm`` and ``inch``.

A dataset-less report have a few uses, but the common case is a report
with at least a detail band::

	import sip
	sip.setapi("QString", 2)

	from PyQt4 import QtGui
	from franq import Report, DetailBand, Function, mm


	class DetailBandReport(Report):
	    margin = (10 * mm, 10 * mm, 10 * mm, 25 * mm)
	    detail = DetailBand(
		dataSet='fruits',
		border=QtGui.QColor("blue"),
		height=5 * mm,
		elements=[
		    Function(top=0 * mm, left=5 * mm, height=5 * mm, width=30 * mm,
		        func=lambda x: x)
		    ])

	app = QtGui.QApplication([])

	r = DetailBandReport()

	printer = QtGui.QPrinter()
	printer.setOutputFileName('detail.pdf')
	fruits = ["Apple", "Orange", "Pear"]
	r.render(printer, fruits=fruits)

In this example, we set the detail band using the *detail* attribute.
That really is a shortcut, and a single section with a single column is
assumed.

A *dataSet* attribute is set with the name of the dataset to use. While
each band can have the dataSet attribute set, the dataset can also be
set in the report itself. Report level bands with no dataset assigned
will use the global dataset. Detail level bands will use the parent
detail bands dataset.

Also, in this example the band height is set, unlike the previous example where
the default was used.

Instead of a Label, a Function element is used. As a simple list of strings is
used as dataset, the function used in the Function element is an "identity"
function.

At the end of the example, note that the dataset is bound in the render() call
as a named parameter using the same name as in the report definition.

All roads leads to Rome
=======================

The previous examples used the same approach to define the report: define a
subclass of report, and set its attributes, band attributes were set to
Band or DetailBand instances. However, several alternatives exists.

A Report can be defined:

* Subclassing the Report class, and setting the attributes at the class level
  as shown above. This is convenient for simple cases.
* Subclassing the Report class, and setting the attributes defining the
  setup() method. setup() is called from __init__(). This approach is good
  for doing inheritance.
* Instancing the Report class, setting its attributes as constructor parameters.
* Instancing the Report class, and next setting its attributes in separate
  sentences.

Bands can be defined:

* Instancing the Band or DetailBand class, setting its attributes as
  constructor parameters (as shown above).
* Subclassing the Band or DetailBand class, setting the attributes at
  the class level.
* Subclassing the Band or DetailBand class, setting the attributes
  overriding the __init__() method.

Also report attributes can be set with either Band instances or Band
subclasses::

	class MyReport(Report):
	    class header(Band):
                height = 10 * mm
                elements = [ ... ]

When a report instance is created, Band subclasses are automatically
instantiated.

Elements
========

There are 3 predefined text elements: ``Label``, ``Function`` and ``Field``.

``Label`` is a simple element to display static text::

	Label(top=0, left=0, width=20 * mm, height=4 * mm, text="Customer name:")

``Function`` displays the result of the callable assigned to the ``func``
parameter. The callable receives the current data item as parameter, it
can return a value generated from the data item, or ignore it and
return a value taken from somewhere else::

        # Prints current date
	Function(top=0, left=155 * mm, width=20 * mm, height=4 * mm,
		func=lambda o: datetime.date.today().strftime('%d/%m/%Y'))

``Field`` does nothing that can't be done with ``Function``, it's just
a convenient way to make clear you are just printing the value of and
attribute of the data item::

	# Print the customer name
	Field(top=0,left=20 * mm, width=30 * mm, heigth=4 * mm,
		attrName='customer.name')

In this example, we are traversing the ``customer`` attribute of the data
item to print the name of the customer, using dot notation.

If a ``formatStr`` parameter is provided, the value is formatted using
``str.format`` instead regular Python 2 ``unicode`` or Python 3 ``str``.

Complex Reports
===============

Simpler, single detail, single column reports can be defined assigning
a ``DetailBand`` to the ``detail`` attribute of the report. Reports
requiring more than one ``DetailBand`` and/or more than a single column
requires defining the detail bands inside a ``Section`` object::

	class DetailBandReport(Report):
           ...
	   sections = [
		Section(
		    columns=2,
		    detailBands=[
		        DetailBand(
		            dataSet='data',
		            height=5 * mm,
		            columnSpace=10 * mm,
		            elements=[
		                Function(top=0 * mm, left=0 * mm,
		                    height=5 * mm, width=30 * mm,
		                    func=lambda x: x[0]),
		                Function(top=0 * mm, left=30 * mm,
		                    height=5 * mm, width=30 * mm,
		                    func=lambda x: x[1])
		            ]
		        )
		    ]
		)
	    ]

In this example, there is a single section with two columns holding a single
detail, but multiple details per section can be defined in the section's
detailBands attribute, and multiple sections per report can be defined in
the report's sections attribute.

Please note that each new section triggers a page break.

Events
======

``Report`` objects, ``Band`` objects and ``Element`` objects can have
attached an ``on_before_print`` event. For the ``Report`` object,
the event callback receives no parameters. For ``Band`` and ``Element``
receives the sender object and the current data item being processed.

Inheritance
===========

The best approach to augment an existent report by subclassing
probably is using the ``setup()`` method, as it makes easily available


Utilities
=========

``counter()`` is a generator that yields a sequence of numbers. Its primary
purpose is to provide numbers for page numbering.

