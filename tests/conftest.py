import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command

@pytest.fixture(scope='session')
def alembic_cfg():
    alembic_cfg = Config(os.path.abspath(os.path.join(os.path.dirname(__file__), '../alembic.ini')))
    alembic_cfg.set_main_option('sqlalchemy.url', 'sqlite:///./test.db')
    alembic_cfg.set_main_option('script_location', os.path.join(os.path.dirname(__file__), '../alembic'))
    return alembic_cfg

@pytest.fixture(scope='session')
def db_engine(alembic_cfg):
    engine = create_engine(alembic_cfg.get_main_option('sqlalchemy.url'))
    return engine

@pytest.fixture(scope='session')
def setup_database(alembic_cfg, db_engine):
    command.upgrade(alembic_cfg, 'head')

    yield

    db_engine.dispose()
    if os.path.exists('test.db'):
        os.remove('test.db')

@pytest.fixture(scope='function')
def db_session(db_engine, setup_database):
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()