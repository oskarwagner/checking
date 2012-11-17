import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, "README.txt")).read()
CHANGES = open(os.path.join(here, "CHANGES.txt")).read()


setup(name="checking",
      version="1.0",
      description="checking",
      long_description=README + "\n\n" +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: BFG",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author="Wichert Akkerman",
      author_email="wichert@wiggy.net",
      url="",
      keywords="invoicing administration",
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      zip_safe=False,
      test_suite="checking",
      message_extractors = {"checking": [
                    ("**.py", "chameleon_python", None),
                    ("**.pt", "chameleon_xml", None),
                    ]},
      install_requires = [
          "repoze.bfg",
          "translationstring >=0.3",
          "SQLAlchemy >=0.6beta3",
          "Chameleon <2dev",
          "transaction",
          "repoze.tm2",
          "zope.sqlalchemy",
          "Babel",
          "pytz",
          "formish",
          "schemaish",
          "validatish",
          "z3c.rml",
          "Pillow",
          ],
      entry_points = """\
      [paste.app_factory]
      main = checking.run:main

      [paste.app_install]
      app = paste.script.appinstall:Installer
      """
      )
