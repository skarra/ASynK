#!/usr/bin/python
## 
## utils.py
##
## Created       : Tue Jul 26 06:54:41  2011
## Last Modified : Tue Jul 26 08:09:40  2011
## 
## Copyright (C) 2011 by Sriram Karra <karra.etc@gmail.com>
## All rights reserved.
## 
## Licensed under the GPL v3
## 

def get_link_rel (links, rel):
    for link in links:
        if link.rel == rel:
            return link.href

    return None
