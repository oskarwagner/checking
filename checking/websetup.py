import transaction
from checking import models
from checking import run

def populate_database():
    session = models.DBSession()
    model = models.Model(name=u'root')
    session.add(model)


def setup_app(command, conf, vars):
    run.app({}, **conf)
    models.Base.metadata.create_all(models.Base.metadata.bind)
    populate_database()
    transaction.get().commit()

