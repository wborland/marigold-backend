
from tests import BaseTestCase
import time, datetime
from dateutil import parser
import json


class MedsTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.fake_user()

    def add_med(self, **kwargs):
        return self.auth_post('/meds/add', kwargs)

    def lookup_med(self, name):
        return self.auth_post('/meds/lookup', dict(name=name))

    def search(self, symptom):
        return self.auth_post('/meds/search', dict(symptom=symptom))

    def get_meds(self):
        return self.auth_get('/meds/for-user')

    def pic(self, picture):
        return self.auth_post('/meds/pic',dict(photo=picture))

    def autoadd_med(self, med_name, **kwargs):
        rv = self.lookup_med(med_name)

        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)

        self.assertEqual(data["message"], "ok")
        match = data["matches"][0]
        
        notifications = kwargs.get("notifications") if "notifications" in kwargs else [{ "day": 0, "time": "2018-01-01:05:00:00" }]
        rv = self.add_med(
            cui = match["cui"],
            name = match["name"],
            quantity = kwargs.get("quantity") or 10,
            notifications = notifications,
            temporary = kwargs.get("temporary") or False,
            alert_user = kwargs.get("alert_user") or False,
            refill = True 
        )

        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)

        self.assertEqual(data["message"], "ok")

        return rv

    def test_lookup_med(self):
        rv = self.lookup_med("Ibuprofen")

        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)

        self.assertEqual(data["message"], "ok")
        self.assertGreater(len(data["matches"]), 0)

    def test_add_med(self):
        rv = self.lookup_med("Ibuprofen")

        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)

        match = data["matches"][0]

        rv = self.add_med(
            cui = match["cui"],
            name = match["name"],
            quantity = 10,
            notifications = [
                { "day": 2, "time": "2018-01-01:05:00:00" }
            ],
            temporary = True,
            alert_user = True,
            refill = True
        )


        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)

        self.assertEqual(data["message"], "ok")

    def test_temporary_on(self):
        rv = self.lookup_med("Advil")

        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)

        match = data["matches"][0]

        rv = self.add_med(
            cui = match["cui"],
            name = match["name"],
            quantity = 10,
            notifications = [
                { "day": 0, "time": "2018-01-01:16:00:00" }
            ],
            temporary = True,
            alert_user = False,
        )
       
        rv = self.get_meds()

        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)

        med = data["meds"][0]
        self.assertEqual(med["temporary"], 1)

    def test_temporary_off(self):
        rv = self.lookup_med("Advil")

        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)

        match = data["matches"][0]

        rv = self.add_med(
            cui = match["cui"],
            name = match["name"],
            quantity = 10,
            notifications = [
                { "day": 0, "time": "2018-01-01:16:00:00" }
            ],
            temporary = False,
            alert_user = False,
            refill = True
        )

        rv = self.get_meds()

        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)

        med = data["meds"][0]
        self.assertEqual(med["temporary"], 0)

    def test_no_conflicts(self):
        self.autoadd_med("Ibuprofen")
        rv = self.autoadd_med("Zyrtec")

        data = json.loads(rv.data)
        self.assertEqual(len(data["conflicts"]), 0)

    def test_conflicts(self):
        self.autoadd_med("Digoxin")
        rv = self.autoadd_med("Quinidine")

        data = json.loads(rv.data)
        self.assertEqual(len(data["conflicts"]), 1)


    def test_update_meds_name(self):
        self.autoadd_med("Advil")
        rv = self.get_meds()
        new_med_id = json.loads(rv.data)
        med_id = new_med_id['meds'][0]['id']

        update = {"med_id":med_id, "name":"Will"}
        self.auth_post('/update/med', update)

        rvp = self.get_meds()
        new_update_med_id = json.loads(rvp.data)
        update_med_name = new_update_med_id['meds'][0]['name']

        self.assertEqual("Will",update_med_name)


    def test_update_meds_quantity(self):
        self.autoadd_med("Advil")
        rv = self.get_meds()
        new_med_id = json.loads(rv.data)
        med_id = new_med_id['meds'][0]['id']

        update = {"med_id":med_id, "quantity":"9"}
        self.auth_post('/update/med', dict(update))

        rvp = self.get_meds()
        new_update_med_id = json.loads(rvp.data)
        update_med_quantity = new_update_med_id['meds'][0]['quantity']

        self.assertEqual(update_med_quantity,9)


    def test_update_meds_none(self):
        self.autoadd_med("Advil")
        rv = self.get_meds()
        new_med_id = json.loads(rv.data)
        med_id = new_med_id['meds'][0]['id']

        update = {"med_id":med_id}
        self.auth_post('/update/med', dict(update))

        rvp = self.get_meds()
        new_update_med_id = json.loads(rvp.data)

        self.assertEqual(new_med_id, new_update_med_id)


    def test_update_meds_temporary(self):
        self.autoadd_med("Advil")
        rv = self.get_meds()
        new_med_id = json.loads(rv.data)
        med_id = new_med_id['meds'][0]['id']

        update = {"med_id":med_id, "temporary":"1"}
        self.auth_post('/update/med', dict(update))

        rvp = self.get_meds()
        new_update_med_id = json.loads(rvp.data)
        update_med_temporary = new_update_med_id['meds'][0]['temporary']

        self.assertEqual(1,update_med_temporary)

    def test_run_out_1(self):

        quantity = 7
        notifications = [
                { "day": 0, "time": "2018-01-01:16:00:00" },
                { "day": 1, "time": "2018-01-01:16:00:00" },
                { "day": 2, "time": "2018-01-01:16:00:00" },
                { "day": 3, "time": "2018-01-01:16:00:00" },
                { "day": 4, "time": "2018-01-01:16:00:00" },
                { "day": 5, "time": "2018-01-01:16:00:00" },
                { "day": 6, "time": "2018-01-01:16:00:00" }
            ]

        self.autoadd_med("Advil", quantity=quantity, notifications=notifications)
        rv = self.get_meds()
        data = json.loads(rv.data)
        run_out_date = data['meds'][0]['run_out_date']
        check_time = datetime.datetime.now() + datetime.timedelta(days = 13) 


        run_out = parser.parse(run_out_date)

        self.assertEqual(run_out.date(),check_time.date())



    def test_run_out_2(self):

        quantity = 30
        notifications = [
                { "day": 0, "time": "2018-01-01:16:00:00" },
                { "day": 2, "time": "2018-01-01:16:00:00" },
                { "day": 4, "time": "2018-01-01:16:00:00" },
            ]

        self.autoadd_med("Advil", quantity=30, notifications=notifications)
        rv = self.get_meds()
        data = json.loads(rv.data)
        run_out_date = data['meds'][0]['run_out_date']
        check_time = datetime.datetime.now() + datetime.timedelta(days = 88) 


        run_out = parser.parse(run_out_date)
        self.assertEqual(run_out.date(),check_time.date())




    def test_run_out_3(self):

        quantity = 6
        notifications = [
                { "day": 0, "time": "2018-01-01:16:00:00" },
                { "day": 2, "time": "2018-01-01:16:00:00" },
                { "day": 4, "time": "2018-01-01:16:00:00" },
            ]

        self.autoadd_med("Advil", quantity=quantity, notifications=notifications)
        rv = self.get_meds()
        data = json.loads(rv.data)
        run_out_date = data['meds'][0]['run_out_date']
        check_time = datetime.datetime.now() + datetime.timedelta(days = 18) 


        run_out = parser.parse(run_out_date)
        self.assertEqual(run_out.date(),check_time.date())


    def test_run_out_4(self):

        quantity = 7
        notifications = [
                { "day": 0, "time": "2018-01-01:16:00:00" },
                { "day": 1, "time": "2018-01-01:16:00:00" }
            ]

        self.autoadd_med("Advil", quantity=quantity, notifications=notifications)
        rv = self.get_meds()
        data = json.loads(rv.data)
        run_out_date = data['meds'][0]['run_out_date']
        check_time = datetime.datetime.now() + datetime.timedelta(days = 35) 


        run_out = parser.parse(run_out_date)
        self.assertEqual(run_out.date(),check_time.date())



    def test_run_out_5(self):

        quantity = 5
        notifications = [
                { "day": 0, "time": "2018-01-01:16:00:00" },
                { "day": 1, "time": "2018-01-01:16:00:00" },
                { "day": 2, "time": "2018-01-01:16:00:00" },
                { "day": 3, "time": "2018-01-01:16:00:00" },
                { "day": 4, "time": "2018-01-01:16:00:00" },
            ]

        self.autoadd_med("Advil", quantity=quantity, notifications=notifications)
        rv = self.get_meds()
        data = json.loads(rv.data)
        run_out_date = data['meds'][0]['run_out_date']
        check_time = datetime.datetime.now() + datetime.timedelta(days = 11) 


        run_out = parser.parse(run_out_date)
        self.assertEqual(run_out.date(),check_time.date())



    def test_run_out_6(self):

        quantity = 5
        notifications = [

            ]

        self.autoadd_med("Advil", quantity=quantity, notifications=notifications)
        rv = self.get_meds()
        data = json.loads(rv.data)
        run_out_date = data['meds'][0]['run_out_date']
        check_time = datetime.datetime.now() + datetime.timedelta(days = 0) 


        run_out = parser.parse(run_out_date)
        self.assertEqual(run_out.date(),check_time.date())



    def test_run_out_7(self):

        quantity = 10
        notifications = [
                { "day": 0, "time": "2018-01-01:16:00:00" },
                { "day": 1, "time": "2018-01-01:16:00:00" },
                { "day": 2, "time": "2018-01-01:16:00:00" },
                { "day": 3, "time": "2018-01-01:16:00:00" },
                { "day": 4, "time": "2018-01-01:16:00:00" },
            ]

        self.autoadd_med("Advil", quantity=quantity, notifications=notifications)
        rv = self.get_meds()
        data = json.loads(rv.data)
        run_out_date = data['meds'][0]['run_out_date']
        check_time = datetime.datetime.now() + datetime.timedelta(days = 18) 


        run_out = parser.parse(run_out_date)
        self.assertEqual(run_out.date(),check_time.date())



    def test_run_out_8(self):

        quantity = 12
        notifications = [
                { "day": 0, "time": "2018-01-01:16:00:00" },
                { "day": 3, "time": "2018-01-01:16:00:00" },
                { "day": 5, "time": "2018-01-01:16:00:00" }
            ]

        self.autoadd_med("Advil", quantity=quantity, notifications=notifications)
        rv = self.get_meds()
        data = json.loads(rv.data)
        run_out_date = data['meds'][0]['run_out_date']
        check_time = datetime.datetime.now() + datetime.timedelta(days = 40) 


        run_out = parser.parse(run_out_date)
        self.assertEqual(run_out.date(),check_time.date())



    def test_run_out_9(self):

        quantity = 17
        notifications = [
                { "day": 0, "time": "2018-01-01:16:00:00" },
                { "day": 1, "time": "2018-01-01:16:00:00" },
                { "day": 2, "time": "2018-01-01:16:00:00" },
                { "day": 3, "time": "2018-01-01:16:00:00" },
                { "day": 4, "time": "2018-01-01:16:00:00" },
                { "day": 5, "time": "2018-01-01:16:00:00" },
                { "day": 6, "time": "2018-01-01:16:00:00" }
            ]

        self.autoadd_med("Advil", quantity=quantity, notifications=notifications)
        rv = self.get_meds()
        data = json.loads(rv.data)
        run_out_date = data['meds'][0]['run_out_date']
        check_time = datetime.datetime.now() + datetime.timedelta(days = 29) 


        run_out = parser.parse(run_out_date)
        self.assertEqual(run_out.date(),check_time.date())



    def test_run_out_10(self):

        quantity = 5
        notifications = [
                { "day": 0, "time": "2018-01-01:16:00:00" },
                { "day": 1, "time": "2018-01-01:16:00:00" }
            ]

        self.autoadd_med("Advil", quantity=quantity, notifications=notifications)
        rv = self.get_meds()
        data = json.loads(rv.data)
        run_out_date = data['meds'][0]['run_out_date']
        check_time = datetime.datetime.now() + datetime.timedelta(days = 22) 


        run_out = parser.parse(run_out_date)
        self.assertEqual(run_out.date(),check_time.date())

    def test_label_purpose(self):
        self.autoadd_med("Advil")
        rv = self.get_meds()
        
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)

        med = data["meds"][0]
        self.assertEqual(med["purpose"], "Fever reducer/Pain reliever")

    def test_label_brand(self):
        self.autoadd_med("Zoloft")
        rv = self.get_meds()

        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)

        med = data["meds"][0]
        self.assertEqual(med["brand_name"], "Zoloft")

    def test_search_basic(self):
        class_id = "N0000001242" # Fever
        symptom = "Fever"
        
        rv = self.search(symptom)

        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)

        self.assertGreater(len(data["drugs"]), 0)

    def test_search_has_drug(self):
        class_id = "N0000001242" # Fever
        symptom = "Fever"

        rv = self.search(symptom)

        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data)

        drugs = data["drugs"]
        self.assertIn("Advil", drugs)

    def test_pic_lookup_1(self):
        with open("tests/1.txt", "r") as file:
            rv = self.pic(file.read())
            data = json.loads(rv.data)

            self.assertEqual(rv.status_code, 200)

            match = data["message"]
            self.assertEqual(match, "Could not read label successfully.")

    def test_pic_lookup_2(self):
        with open("tests/2.txt", "r") as file:
            rv = self.pic(file.read())
            data = json.loads(rv.data)

            self.assertEqual(rv.status_code, 200)

            match = data["message"]
            self.assertEqual(match, "Could not read label successfully.")

    def test_pic_lookup_3(self):
        with open("tests/3.txt", "r") as file:
            rv = self.pic(file.read())
            data = json.loads(rv.data)

            self.assertEqual(rv.status_code, 200)

            match = data["matches"]
            self.assertEqual(data["message"], "ok")
           
    def test_pic_lookup_4(self):
        with open("tests/4.txt", "r") as file:
            rv = self.pic(file.read())
            data = json.loads(rv.data)

            self.assertEqual(rv.status_code, 200)

            match = data["matches"]
            self.assertEqual(data["message"], "ok")

    def test_pic_lookup_5(self):
        with open("tests/5.txt", "r") as file:
            rv = self.pic(file.read())
            data = json.loads(rv.data)

            self.assertEqual(rv.status_code, 200)

            match = data["matches"]
            self.assertEqual(data["message"], "ok")
