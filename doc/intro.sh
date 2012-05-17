#!/bin/bash

sed s/'@enumerate'/'<ol>'/g | sed s/'@item'/'<li>'/g | sed s/'@end enumerate'/'<\/ol>'/g
