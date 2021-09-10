#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created by jacob.mendt@pikobytes.de on 10.09.21
#
# This file is subject to the terms and conditions defined in file
# "LICENSE", which is part of this source code package
from string import Template

def writeMapfile(targetPath, templatePath, templateValues):
    """ Functions writes a mapfile. It replaces the template with the given params dict.

    :param targetPath: Path of the target file
    :type targetPath: str
    :param templatePath: Path to the template file
    :type templatePath: str
    :param templateValues: Dictionary containing the template values
    :type templateValues: Dict
    :return: Path to template file
    :rtype: str
    """

    # Create new template string
    content = None
    with open(templatePath, 'r') as f:
        src = Template(f.read())
        content = src.substitute(templateValues)

    if content != None:
        with open(targetPath, 'w') as f:
            f.write(content)
    return targetPath