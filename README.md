
# Overview

btsnoopy is a Python 3.x class-based (OOP, yeah! woo! ... *looks around* .. awesome ... *looks around nervously* .. whatever *shrugs*) rewrite of the btsnoop file parser forked from https://github.com/robotika/jessica.

Reasons:

* 2 heads are better than 1. Add another one though... and you have a crowd!
* `assert` statements are scary, actionable errors are better (I think..?)
* parser started getting specific (checking for sent data (flag==0) packet records..?)
  * I'm looking to work with btsnoop files in a more generic manner, specifically to interact with a device from a different vendor.
* vim? *shakes head disappointingly*
