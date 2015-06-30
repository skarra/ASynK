##
## Created       : Thu May 17 13:02:14 IST 2012
## Last Modified : Tue Jun 30 13:31:21 IST 2015
##
## Copyright (C) 2012, 2015 Sriram Karra <karra.etc@gmail.com>
##
## This file is part of ASynK
##
## ASynK is free software: you can redistribute it and/or modify it under
## the terms of the GNU Affero General Public License as published by the
## Free Software Foundation, version 3 of the License
##
## ASynK is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
## FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public
## License for more details.
##
## You should have a copy of the license in the doc/ directory of ASynK.  If
## not, see <http://www.gnu.org/licenses/>.

## Change this to the location of the Info dir file, will be used for
## the install-info target below.
infodir  = ~/elisp/info

##
## You should not have to change anything below this
##

srcdir   = .
texinfo_main  = asynk.texi	# The Master Texinfo file
texinfo_info  = asynk.info
texinfo_intro = intro.texi
texinfo_other = ${texinfo_intro} # Included in texinfo_main
texinfos   = ${texinfo_main} ${texinfo_other}
extra_texi = agpl-3.0.texi doclicense.texi # Third party texis
doc_css = index.css

texinfo_base = ${texinfo_main:.texi=}

text_name    = ${texinfo_base}.txt
pdf_name     = ${texinfo_base}.pdf
ps_name      = ${texinfo_base}.ps
dvi_name     = ${texinfo_base}.dvi
info_name    = ${texinfo_base}.info
xml_name     = ${texinfo_base}.xml
html_dirname = ${texinfo_base}
intro_html   = intro.html

gen_files = ${text_name} ${pdf_name} ${ps_name} ${dvi_name} ${intro_html} ${info_name} ${html_dirname} ${xml_name}

makeinfo = makeinfo
makeinfo_flags = 

texi2html = texi2html
texi2html_flags = --css-include=${doc_css} --split chapter --l2h-clean --output=${html_dirname}

texi2pdf = texi2pdf
texi2pdf_flags = --clean --quiet

intro_sh = ./intro.sh

all: html info docbook text # pdf

html: ${texinfos} ${extra_texi} ${intro_html}
	${texi2html} ${texi2html_flags} ${texinfo_main}

${intro_html}: ${texinfo_intro}
	(cat ${texinfo_intro} | ${intro_sh}) > $@

info: ${texinfos} ${extra_texi}
	${makeinfo} ${makeinfo_flags} ${texinfo_main}
install-info: info
	cp ${texinfo_info} ${infodir}
	install-info --info-file ${infodir}/${texinfo_info} --dir-file ${infodir}/dir

docbook: ${texinfos} ${extra_texi}
	${makeinfo} --docbook ${makeinfo_flags} ${texinfo_main}

text: ${texinfos} ${extra_texi}
	${makeinfo} --plaintext ${makeinfo_flags} ${texinfo_main} > ${text_name}

pdf: ${texinfos} ${extra_texi}
	${texi2pdf} ${texi2pdf_flags} --output=${pdf_name} ${texinfo_main}

clean:
	rm -rf ${gen_files}

distclean: clean
	rm -f *~
