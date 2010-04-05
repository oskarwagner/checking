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
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite="checking",
      install_requires = [
          "repoze.bfg",
          "SQLAlchemy >=0.6beta3",
          "transaction",
          "repoze.tm2",
          "zope.sqlalchemy",
          "Babel",
          "pytz",
          "formish",
          "schemaish",
          "validatish",
          ],
      entry_points = """\
      [paste.app_factory]
      app = checking.run:app

      [paste.app_install]
      app = paste.script.appinstall:Installer
      """
      )
