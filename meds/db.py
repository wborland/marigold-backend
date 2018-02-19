
from datetime import datetime

import db
import auth

from error import Error

id_field = 0
name_field = 1
dose_field = 2
expir_date = 3

class InvalidDose(Error):
    """Dose is not a parsable integer"""
    status_code = 400
    error_code = 30

class InvalidDate(Error):
    """Dose is not a parsable integer"""
    status_code = 400
    error_code = 31

add_cmd = """
    INSERT INTO meds (name, dose, expir_date, uid)
    VALUES (%s, %s, %s, %s);
"""

def add(name, dose, expir_date):
    conn = db.conn()
    cursor = conn.cursor()

    try:
        dose_parsed = int(dose)
    except:
        raise InvalidDose()

    try:
        expir_parsed = datetime.strptime(expir_date, '%m %d %Y')
    except:
        raise InvalidDate()

    cursor.execute(add_cmd, [name, dose_parsed, expir_parsed, auth.uid()])
    conn.commit()


for_user_cmd = """
    SELECT id, name, dose, expir_date FROM meds
    WHERE uid = %s
"""

def for_user():
    conn = db.conn()
    cursor = conn.cursor(db.DictCursor)
    
    cursor.execute(for_user_cmd, [auth.uid()])
    users_meds = cursor.fetchall()
   
    return users_meds


class MedIdNotFound(Error):
    """Given medicine ID was not in the database"""
    status_code = 400
    error_code = 32

delete_cmd = """
   DELETE FROM meds
   WHERE id = %s
"""

def delete(med_id):
    conn = db.conn()
    cursor = conn.cursor()

    count = cursor.execute(delete_cmd, [med_id])
    if count == 0:
        raise MedIdNotFound()

    conn.commit()