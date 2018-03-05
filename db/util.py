
import MySQLdb as sql
import hashlib

import db
import auth

tables = {}

tables["users"] = """
    CREATE TABLE {} (
        id int(11) NOT NULL AUTO_INCREMENT,

        first_name varchar(256) NOT NULL,
        last_name varchar(256) NOT NULL,

        email varchar(256) NOT NULL,
        password varchar(256) NOT NULL,

        league varchar(256),

        PRIMARY KEY(id)
    );
"""

tables["user_meds"] = """
    CREATE TABLE {} (
        id int NOT NULL AUTO_INCREMENT,

        name mediumtext NOT NULL,
        dose int NOT NULL,
        quantity int NOT NULL,

        run_out_date date NOT NULL, 

        uid int NOT NULL,
        mid int,
       
        PRIMARY KEY(id)
    );
"""

tables["meds"] = """
    CREATE TABLE {} (
        id int NOT NULL AUTO_INCREMENT,

        name mediumtext NOT NULL,
        dose int(11) NOT NULL,
        expir_date date NOT NULL,

        uid int(11) NOT NULL,
       
        PRIMARY KEY(id)
    );
"""

def init():
    """
    Creates tables
    """
    conn = db.conn()
    cursor = conn.cursor()

    for name, cmd in tables.items():
        drop_cmd = "DROP TABLE IF EXISTS {};".format(name)

        try:
            cursor.execute(drop_cmd)
            cursor.execute(cmd.format(name))
        except sql.Error as err:
            print(err)

def add_user(first, last, email, passwd):
    conn = db.conn()
    cursor = conn.cursor()

    cmd = """
        INSERT INTO users (first_name, last_name, email, password)
        VALUES ('{}', '{}', '{}', '{}');
    """.format(first, last, email, auth.calc_hash(passwd))

    try:
        cursor.execute(cmd)
    except sql.Error as err:
        print(err)

    conn.commit()
    
