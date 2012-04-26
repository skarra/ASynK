dnl Process this file with autoconf to produce a new configure script

AC_PREREQ([2.64])

AC_INIT([asynk],[v0.01+],[karra.etc@gmail.com])

AC_COPYRIGHT([Copyright (C) 2011-2012 Sriram Karra <karra.etc@gmail.com>.])

AM_INIT_AUTOMAKE([foreign])

if test x"$texmfdir" = x; then
  AC_MSG_WARN([texmfdir not set, TeX files will not be installed.
      For potential values for texmfdir, run: kpsewhich -show-path .tex])
fi
AC_SUBST(texmfdir)
AM_CONDITIONAL([HAVE_TEXMF], test x"${texmfdir}" != x)

AC_CONFIG_FILES([Makefile
		doc/Makefile])

AC_OUTPUT
