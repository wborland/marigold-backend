
from flask import request, jsonify, Blueprint

import auth
from error import Error, MissingDataError

import meds.db
import meds.lookup
import meds.conflict
import meds.fda
import meds.by_symptom

blueprint = Blueprint("meds", __name__)

@blueprint.route('/lookup', methods = ['POST'])
@auth.required
def lookup():
    data = request.get_json()
        
    try:
        name = data["name"]
    except KeyError as err:
        raise MissingDataError(err)

    matches = meds.lookup.perform(name)
    return jsonify(message="ok", matches=matches)

@blueprint.route('/search', methods = ['POST'])
@auth.required
def search():
    data = request.get_json()
        
    try:
        class_id = data["class_id"]
    except KeyError as err:
        raise MissingDataError(err)

    drugs = meds.by_symptom.perform(class_id)
    return jsonify(message="ok", drugs=drugs)

@blueprint.route('/add', methods = ['POST'])
@auth.required
def add():
    data = request.get_json()
        
    try:
        cui = data["cui"]
        name = data["name"]
        quantity = data["quantity"]
        notifications = data["notifications"]
        temporary = data["temporary"]
        alert_user = data["alert_user"]
    except KeyError as err:
        raise MissingDataError(err)


    meds.db.add(name, cui, quantity, notifications, temporary, alert_user)
    return jsonify(message="ok", conflicts=meds.conflict.check())

@blueprint.route('/for-user', methods = ['GET'])
@auth.required
def for_user():
    users_meds = meds.db.for_user()
    return jsonify(message="ok", meds=users_meds)

@blueprint.route('/conflicts', methods = ['GET'])
@auth.required
def conflicts():
    conflicts = meds.conflict.check()
    return jsonify(message="ok", conflicts=conflicts)

@blueprint.route('/refill', methods = ['POST'])
@auth.required
def refill():
    data = request.get_json()

    try:
        med_id = data["med_id"]
    except KeyError as err:
        raise MissingDataError(err)

    meds.db.refill(med_id)
    return jsonify(message="ok")

@blueprint.route('/delete', methods = ['POST'])
@auth.required
def delete():
    data = request.get_json()

    try:
        med_id = data["id"]
    except KeyError as err:
        raise MissingDataError(err)

    meds.db.delete(med_id)
    return jsonify(message="ok")
