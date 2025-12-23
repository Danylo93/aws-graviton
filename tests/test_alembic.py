from alembic import command

def test_migrations_upgrade(db_session, alembic_cfg):
    command.upgrade(alembic_cfg, 'head')

def test_migrations_downgrade(db_session, alembic_cfg):
    command.upgrade(alembic_cfg, 'head')
    command.downgrade(alembic_cfg, 'base')

def test_data_integrity(db_session, alembic_cfg):
    command.upgrade(alembic_cfg, 'head')

    from sqlalchemy import Table, Column, Integer, String, MetaData
    metadata = MetaData()
    example_table = Table('categories', metadata,
                          Column('id', Integer, primary_key=True),
                          Column('category_name', String))
    db_session.execute(example_table.insert(), {'id': 1, 'category_name': 'Test'})

    result = db_session.execute(example_table.select()).fetchall()
    assert len(result) == 1
    assert result[0][1] == 'Test'

