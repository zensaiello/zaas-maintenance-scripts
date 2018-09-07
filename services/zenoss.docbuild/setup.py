from setuptools import setup, find_packages

setup(
    name="zenoss.docbuild",
    version="0.1.1",
    description="ZenPack Documentation Builder",
    author="Zenoss Professional Services",
    author_email="ps@zenoss.com",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['zenoss'],
    package_data={
        "zenoss.docbuild": [
            "static/*",
        ],
    },
    data_files=[
        ("/etc", ["zenoss-docbuild.conf"]),
        ("/etc/init.d", ["scripts/zenoss-docbuild"]),
    ],
    scripts=["scripts/zenoss-docbuild.py"],
    install_requires=[
        "Twisted-web>=8.2.0",
        "PyYAML",
        "docutils",
        "pyopenssl",
        "pypandoc",
    ],
    zip_safe=False,
)

