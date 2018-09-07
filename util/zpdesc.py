#!/usr/bin/env python

import sys
import urllib
import posixpath
import xml.sax

import docutils.core

import yaml


TS = " " * 4

def process(location):
    location = location.rstrip("/")

    github = False
    if location.startswith("https://github.com"):
        location = location.replace("https://github.com", "https://raw.githubusercontent.com")
        github = True

    packname = location.split("/")[-1].split("-")[0]
    if github:
        location = posixpath.join(location, "master")
    deviceClassData = {}

    locationParts = [location] + packname.split(".")
    location = posixpath.join(*locationParts)

    components = [
        ("zenpack.yaml", processYaml),
        ("objects/objects.xml", processXml),
    ]
    for subpath, fn in components:
        path = posixpath.join(location, subpath)
        try:
            fh = urllib.urlopen(path)
        except IOError:
            continue

        try:
            fn(deviceClassData, fh)
        finally:
            fh.close()

    return packname, deviceClassData

def addItems(deviceClassData, deviceClassName, templateName, type_, items):
    if items:
        deviceClassDatum = deviceClassData.setdefault(deviceClassName, {})
        templateData = deviceClassDatum.setdefault(templateName, {})
        templateData.setdefault(type_, []).extend(items)

def processYaml(deviceClassData, fh):
    document = yaml.load(fh)

    for deviceClassName, deviceClass in document.get("device_classes", {}).items():
        deviceClassName = "Devices" + deviceClassName
        for templateName, template in deviceClass.get("templates", {}).items():

            datasources = template.get("datasources", {})
            for datasource in datasources.values():
                datapoints = datasource.get("datapoints", {}).keys()
                addItems(deviceClassData, deviceClassName, templateName, "Datapoints", datapoints)

            thresholds = template.get("thresholds", {}).keys()
            addItems(deviceClassData, deviceClassName, templateName, "Thresholds", thresholds)

def processXml(deviceClassData, fh):
    handler = _ObjectxXmlHandler(deviceClassData)
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)
    parser.parse(fh)

class _ObjectxXmlHandler(xml.sax.ContentHandler):
    def __init__(self, deviceClassData):
        self.deviceClassData = deviceClassData
        self.deviceClass = ""
        self.templateName = ""
        self.path = []

    def startElement(self, name, attrs):
        if name == "object":
            if attrs["class"] == "RRDTemplate":
                self.templateName = attrs["id"].split("/")[-1]
            elif self.path and self.path[-1] in ["datapoints", "thresholds"]:
                deviceClassName = posixpath.join(*self.path).lstrip("/zport/dmd/").split("/rrdTemplates")[0]
                addItems(
                    self.deviceClassData,
                    deviceClassName,
                    self.templateName,
                    self.path[-1].capitalize(),
                    [attrs["id"]],
                )

        if name != "objects":
            self.path.append(attrs["id"])

    def endElement(self, name):
        if name != "objects":
            self.path.pop()

def rstify(name, data):
    result = ""
    result += "=" * len(name) + "\n"
    result += name + "\n"
    result += "=" * len(name) + "\n"

    for deviceClassName, deviceClassDatum in data.iteritems():
        deviceClassName = deviceClassName
        result += deviceClassName + "\n"
        result += "-" * len(deviceClassName) + "\n"

        for templateName, templateData in deviceClassDatum.iteritems():
            result += "* " + templateName + "\n"
            for type_, items in templateData.items():
                result += TS + "* " + type_.capitalize() + "\n"
                result += ("\n" + TS * 2 + "* ").join([""] + items).lstrip("\n") + "\n"
        result += "\n"

    return result

if __name__ == "__main__":
    format, location = sys.argv[1:]
    name, data = process(location)
    rst = rstify(name, data)
    print docutils.core.publish_string(rst, writer_name=format)


