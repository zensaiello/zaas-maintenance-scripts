#!/usr/bin/env python

import posixpath

import yaml

# Note: pypandoc requires pandoc to be installed, which may require "yum install pandoc"
import pypandoc
import tempfile
import os

from functools import partial

from docutils.core import publish_string

from twisted.python import failure


README = "README.rst"
TS = " " * 4
DEFAULT_TYPE = "rst"


def checkFailure(fn):
    def inner(self, result, **kwargs):
        if isinstance(result, failure.Failure):
            return
        headers, contents = result
        if len(contents) < 80:
            return
        fn(self, contents, **kwargs)
    return inner


class ZenPackDocBuilder(object):

    def __init__(self, reponame=""):
        self._contents = {}
        self._aliases = []
        self._processors = []
        self._onedocfound = False
        self._outfile = None
        self._appendVersionToOutfile = False
        # Build defaults
        defaultpath = reponame.replace(".", "/")
        for filename, paths, ptype, options in [  # ("setup.py", [""], "about", {}),
                                                # by default we search for readmes in 2 locations,
                                                # if 2 actually exist one overwrites the other
                                                ("README.rst", ["", defaultpath], "rst", {"remove_toc": True}),
                                                ("zenpack.yaml", [defaultpath], "zenpacklib_yaml", {})]:
            self._aliases.append(filename)
            self._contents[filename] = ""
            for path in paths:
                pt = self._getProcessorTuple(filename, filename, path, ptype, options)
                if pt:
                    self._processors.append(pt)

    def buildProcessorsFromDocYaml(self, contents, documentname):
        documents = yaml.load(contents).get("documents", {})
        document = documents.get(documentname, {})
        # wipe existing order and docs created in init
        orderdefined = False
        self._outfile = document.get("outfile", "{0}-zenpackdoc".format(documentname))
        options = document.get("options", {})
        self._appendVersionToOutfile = options.get("appendVersionToOutfile",
                                                   True)
        order = document.get("order", [])
        if order:
            orderdefined = True
            self._aliases = order
        docs = []
        for docAlias, doc in document.get("sources", {}).items():
            # initialize
            self._contents[docAlias] = ""
            pt = self._getProcessorTuple(docAlias, doc.get("filename", ""), doc.get("path", ""), doc.get("type", DEFAULT_TYPE), doc.get("options", {}))
            if pt:
                docs.append(pt)

            if not orderdefined:
                self._aliases.append(docAlias)

        self._processors = docs

    @checkFailure
    def getReadme(self, contents, alias="README.rst", options={}):
        lines = contents.splitlines()
        contents = ""
        for line in lines:
            if not (options.get('remove_toc', False) and (line == ".. contents::" or " :depth:" in line)):
                contents += line + "\n"
        self._onedocfound = True
        self._contents[alias] = contents

    @checkFailure
    def getMonitoring(self, contents, alias="zenpack.yaml", options={}):
        document = yaml.load(contents)

        deviceClassData = {}
        modelers = None
        for deviceClassName, deviceClass in document.get("device_classes", {}).items():
            deviceClassName = "Devices" + deviceClassName

            for zPropertyName, zProperty in deviceClass.get("zProperties", {}).items():
                if zPropertyName == "zCollectorPlugins":
                    modelers = zProperty

            for templateName, template in deviceClass.get("templates", {}).items():

                datasources = template.get("datasources", {})
                for datasource in datasources.values():
                    datapoints = datasource.get("datapoints", {}).keys()
                    _addItems(deviceClassData, deviceClassName, templateName, "Datapoints", datapoints)

                thresholds = template.get("thresholds", {}).keys()
                _addItems(deviceClassData, deviceClassName, templateName, "Thresholds", thresholds)

                graphs = template.get("graphs", {}).keys()
                _addItems(deviceClassData, deviceClassName, templateName, "Graphs", graphs)

        # component classes
        # can't tell what's a component class, a device, and a base class in classes but...
        # a component class is most always on the right hand side of a relationship
        # so we get a unique list of those and use their class label if defined
        compClasses = set()
        classes = document.get("classes", {})
        for rel in document.get("class_relationships", []):
            c = rel.split(' ')[-1]
            label = classes.get(c, {}).get("label")
            if label:
                compClasses.add(label)
            else:
                compClasses.add(c)

        result = ""
        if not deviceClassData:
            return result

        if modelers:
            result = "Modeler Plugins\n"
            result += "---------------\n\n"
            for modeler in modelers:
                result += "* " + modeler + "\n"
            result += '\n'

        if compClasses:
            result += "Components Modeled\n"
            result += "------------------\n\n"
            for c in compClasses:
                result += "* " + c + "\n"
            result += '\n'

        result += "Device Class Templates\n"
        result += "----------------------\n\n"

        for deviceClassName, deviceClassDatum in deviceClassData.iteritems():
            deviceClassName = deviceClassName
            result += deviceClassName + "\n"
            result += "=" * len(deviceClassName) + "\n\n"

            for templateName, templateData in deviceClassDatum.iteritems():
                result += "* " + templateName + "\n\n"
                for type_, items in templateData.items():
                    result += TS + "* " + type_.capitalize() + "\n\n"
                    result += ("\n" + TS * 2 + "* ").join([""] + items).lstrip("\n") + "\n"
            result += "\n"

        self._onedocfound = True
        self._contents[alias] = result

    @checkFailure
    def getAbout(self, contents, alias="setup.py", options={}):
        """ about zenpack based on what is in the setup.py file"""
        addtorequires = False
        requires_string = ""
        requires = None
        lines = contents.splitlines()
        keepReading = True
        length = len(lines)
        index = 0
        while keepReading and index < length:
            line = lines[index]
            if lines[index].startswith("# STOP_REPLACEMENTS"):
                keepReading = False
            elif addtorequires:
                requires_string += line.strip()
                if ']' in line:
                    addtorequires = False
                    try:
                        requires = eval(requires_string)
                    except SyntaxError:
                        # swallow
                        pass
            elif line.startswith("NAME =") or line.startswith("NAME="):
                name = line.split("=")[1]
                zenpackname = name.strip().strip('"').strip("'")
            elif line.startswith("VERSION =") or line.startswith("VERSION="):
                name = line.split("=")[1]
                version = name.strip().strip('"').strip("'")
            elif line.startswith("AUTHOR =") or line.startswith("AUTHOR="):
                name = line.split("=")[1]
                author = name.strip().strip('"').strip("'")
            elif line.startswith("INSTALL_REQUIRES =") or line.startswith("INSTALL_REQUIRES="):
                name = line.split("=")[1]
                requires_string = name.strip()
                if ']' not in name:
                    addtorequires = True
            index += 1

        result = ""
        nameLen = len(zenpackname)
        result += ("=" * nameLen) + "\n"
        result += zenpackname + "\n"
        result += ("=" * nameLen) + "\n\n"
        result += ("Version") + "\n"
        result += ("-" * 7) + "\n\n"
        result += version + "\n\n"
        result += ("Author") + "\n"
        result += ("-" * 6) + "\n\n"
        result += author + "\n\n"

        if requires:
            result += ("Install Requires") + "\n"
            result += ("-" * 16) + "\n\n"
            for package in requires:
                result += package + "\n\n"
            result += "\n"

        if self._appendVersionToOutfile:
            self._outfile = "{}{}".format(self._outfile, version)

        self._onedocfound = True
        self._contents[alias] = result

    def nothingFound(self):
        if not self._onedocfound:
            return True
        # todo look through contents and see if its empty

    def generateDoc(self, outputType):
        buffer_ = ""
        for filename in self._aliases:
            buffer_ += self._contents[filename] + "\n"

        output = publish_string(
            source=buffer_,
            parser_name="restructuredtext",
            writer_name=outputType,
        )
        return output

    def generatePanDoc(self, outputType):
        buffer_ = ""
        for filename in self._aliases:
            buffer_ += self._contents[filename] + "\n"
        output = pypandoc.convert_text(
            buffer_,
            outputType,
            format='rst')
        return output

    def generatePanDocFile(self, outputType, outputFilename):
        """"  This is the only way to convert to some output formats (e.g. odt, docx, epub, epub3, pdf) """
        # default PDF requires LaTeX, which may require "yum install texlive" etc...
        buffer_ = ""
        for filename in self._aliases:
            buffer_ += self._contents[filename] + "\n"

        with tempfile.NamedTemporaryFile(delete=False) as fh:
            # it was observed on the jenkins server "svcbuild.zenoss.loc"
            # when the jenkins user ran this without explicitly handling
            # the delete of the temp file, a 0 byte PDF was created
            try:
                fh.write(buffer_)
                fh.close()
                if outputType == "pdf":
                    ea = ['-V', 'geometry:margin=1.5cm']
                else:
                    ea = []
                pypandoc.convert_file(fh.name, outputType, format='rst',
                                      outputfile=outputFilename, extra_args=ea)
            finally:
                os.remove(fh.name)

    def getProcessors(self):
        return self._processors

    def _getProcessorTuple(self, alias, filename, path, ptype, options):
        processor = self.TYPE_PROCESSORS.get(ptype)
        if processor == "nofunc":
            return None
        fn = partial(getattr(self,
                             processor),
                     alias=alias,
                     options=options)
        fullpath = posixpath.join(path, filename)
        return (fullpath, fn)

    TYPE_PROCESSORS = {"rst": "getReadme",
                       "zenpacklib_yaml": "getMonitoring",
                       "about": "getAbout",
                       # TODO: define something better to deal with md
                       "md": "getReadme",
                       # TODO: removed topofdoc func but since there's logic
                       # to allow defining a function call rather than pasting
                       # whats in a file, I'm leaving this here as a placeholder
                       # when an appropriate func is defined 
                       "topofdoc": "nofunc"}


def _addItems(deviceClassData, deviceClassName, templateName, type_, items):
    if items:
        deviceClassDatum = deviceClassData.setdefault(deviceClassName, {})
        templateData = deviceClassDatum.setdefault(templateName, {})
        templateData.setdefault(type_, []).extend(items)

