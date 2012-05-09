info_TEXINFOS = asynk.texi
doc_DATA = asynk.pdf
MOSTLYCLEANFILES = asynk.info
extra_texi = doclicense.texi gpl.texi

asynk.info asynk.pdf: $(extra_texi)
EXTRA_DIST = $(extra_texi)
AM_MAKEINFOFLAGS = --css-include=index.css
DIST_SOURCES = index.css
