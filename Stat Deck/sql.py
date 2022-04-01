import sqlite3
import os

'''
Since multiple users can make sql calls at the same time we use a sql pool of db connections.
It is essential to maintain calls on a differenct connection so that when one connection is 
writing all other connections are locked out, which is done automatically by the sqlite3 library.
This prevents data corruption and other issues that occur with combining multi threading and sql.
Additionally, we can avoid having to open a new connection with each requests.
'''
class SqlPool:
    def __init__(self, num_pools):
        self.pools = [] #Connection queue using Most recently used replacement policy
        for x in range(num_pools):
           connection = sqlite3.connect(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data/user.db'), check_same_thread=False) 
           cursor = connection.cursor()
           self.pools.append((connection, cursor))

    def get_db(self):
        if not self.pools:
            raise EmptyPoolError()
        return self.pools.pop()

    def commit(self, con_tuple):
        con_tuple[0].commit()
        self.pools.append(con_tuple)

class EmptyPoolError(Exception):
    def __init__(self, message="SQL pool is empty. Unable to provide connection."):
        self.message = message
        super().__init__(self.message)