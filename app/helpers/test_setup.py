try:
    from conf import Conf
except ImportError:
    from ..conf import Conf

import os


def setup_fixture():
    # Clean the map db from MongoDb
    if Conf.Instance().APP_MODE == "Test_Aws":
        os.system('service mongod stop')
        os.system('rm -Rf /data-mongodb/rs0-1/*')
        os.system('rm -Rf /data-mongodb/rs0-2/*')
        os.system('rm -Rf /data-mongodb/rs0-3/*')
        os.system('service mongod start')
    else:
        os.system('mongo map --eval "db.dropDatabase()"')

    # Clean the SqlLite Db
    sql_db = Conf.Instance().SQLITE_DB
    os.system('rm -Rf sql_db %s' % sql_db)
