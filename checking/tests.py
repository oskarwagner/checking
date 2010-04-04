import unittest
from repoze.bfg.configuration import Configurator
from repoze.bfg import testing

class TestMyView(unittest.TestCase):
    def setUp(self):
        from checking.models import setup_engine
        from checking.models import Base

        self.config = Configurator()
        self.config.begin()
        setup_engine({'sqlalchemy.url': 'sqlite://'})
        Base.metadata.create_all()

    def tearDown(self):
        from checking.models import Base
        from checking.models import DBSession
        DBSession.remove()
        Base.metadata.drop_all()
        self.config.end()

    def test_it(self):
        from checking.websetup import populate_database
        from checking.views import my_view
        populate_database()
        request = testing.DummyRequest()
        info = my_view(request)
        self.assertEqual(info['root'].name, 'root')
        self.assertEqual(info['project'], 'checking')
