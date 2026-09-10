"""
Tier 4: Real-World Multi-Student Application Scenarios
Simulates realistic, multi-student campus sharing workflows at KUET:
- Scenario 1: Inter-Department Lab Equipment Sharing (CSE lends multimeter to EEE, on-time return, 5-star review)
- Scenario 2: Overdue Coursebook Loan & Late Return Penalty Cascade (ME lends book to CE, late return, -30 penalty)
- Scenario 3: High-Demand Sensor Beacon & Competing Requests Resolution (BME item, competing CSE/ECE requests)
- Scenario 4: End-to-End Discovery, Campus Map Coordinates, Direct Chat & Handover Journey
- Scenario 5: Defective Item Reporting & Student Safety Moderation Audit
Total: 5 complete scenarios
"""

import datetime
from tests.base import BaseE2ETestCase
from app import models


class TestTier4Scenarios(BaseE2ETestCase):

    def test_scenario_1_inter_department_lab_equipment_sharing(self):
        """Scenario 1: CSE student lends Fluke Multimeter to EEE student with on-time return and 5-star review."""
        # 1. Onboarding: Tanvir (CSE, Batch 21) and Anik (EEE, Batch 22)
        tanvir, _, tanvir_h = self.register_and_login(
            name="Tanvir Hossain",
            email="tanvir2107001@stud.kuet.ac.bd",
        )
        self.assertEqual(tanvir["dept"], "CSE")
        self.assertEqual(tanvir["karma"], 100)

        anik, _, anik_h = self.register_and_login(
            name="Anik Sen",
            email="anik2203015@stud.kuet.ac.bd",
        )
        self.assertEqual(anik["dept"], "EEE")
        self.assertEqual(anik["karma"], 100)

        # 2. Listing: Tanvir posts Fluke 115 Digital Multimeter
        item = self.create_item(
            auth_headers=tanvir_h,
            title="Fluke 115 True RMS Digital Multimeter (Exam Approved)",
            category="Electronics",
            type="lend",
            specs="6000 count resolution, CAT III 600V safety rated, true RMS AC measurement",
            condition="Excellent",
            zone="cse_bldg",
            latitude=22.9003,
            longitude=89.5024,
            description="Available for midterm and final sessionals. Clean leads and fresh 9V battery included.",
            tags=["#Multimeter", "#Fluke", "#CSE", "#LabReady"],
        )
        self.assertTrue(item["is_available"])

        # 3. Discovery & Borrow Request: Anik searches for "Fluke", finds item, and submits borrow request
        search_results = self.client.get("/api/items", params={"search": "Fluke"}).json()
        self.assertEqual(len(search_results), 1)
        found = search_results[0]
        self.assertEqual(found["owner"]["name"], "Tanvir Hossain")

        req_resp = self.create_borrow_request(
            auth_headers=anik_h,
            item_id=found["id"],
            duration_hours=24,
            purpose="Circuits II Lab Final Sessional (EEE 2202)",
            pickup_zone="cse_bldg",
            message="Hi Tanvir, need this for my EEE sessional exam tomorrow morning. Will return by 5pm.",
        )
        self.assertEqual(req_resp.status_code, 200)
        req = req_resp.json()

        # 4. Acceptance: Tanvir accepts Anik's borrow request
        accept_resp = self.client.put(
            f"/api/requests/{req['id']}/status",
            json_data={"status": "accepted"},
            headers=tanvir_h,
        )
        self.assertEqual(accept_resp.status_code, 200)

        # 5. Handover: Tanvir starts transaction at CSE building lobby, generates 4-digit OTP & QR code
        start_resp = self.client.post(
            "/api/transactions/start",
            json_data={"request_id": req["id"]},
            headers=tanvir_h,
        )
        self.assertEqual(start_resp.status_code, 200)
        otp = start_resp.json()["otp"]
        self.assertIsNotNone(start_resp.json()["qr_code"])

        # Anik verifies physical handover
        verify_resp = self.client.post(
            "/api/transactions/verify",
            json_data={"request_id": req["id"], "otp": otp},
            headers=anik_h,
        )
        self.assertEqual(verify_resp.status_code, 200)

        # 6. Return: Anik finishes exam and confirms return on time
        return_resp = self.client.post(f"/api/transactions/return/{req['id']}", headers=anik_h)
        self.assertEqual(return_resp.status_code, 200)
        karma_data = return_resp.json()["karma_updated"]
        self.assertTrue(karma_data["is_on_time"])
        self.assertEqual(karma_data["owner_gain"], 10)
        self.assertEqual(karma_data["borrower_change"], 5)

        # 7. Peer Review: Anik submits glowing 5-star review for Tanvir
        review_resp = self.client.post(
            "/api/reviews",
            json_data={
                "reviewee_id": tanvir["id"],
                "rating": 5,
                "comment": "Thanks Tanvir! The multimeter was perfectly calibrated and battery was full. A+ lender!",
            },
            headers=anik_h,
        )
        self.assertEqual(review_resp.status_code, 200)

        # 8. Verification: Check Tanvir's public profile
        tanvir_profile = self.client.get(f"/api/auth/user/{tanvir['id']}").json()
        self.assertEqual(tanvir_profile["karma"], 110)
        self.assertEqual(tanvir_profile["total_lends"], 1)

        reviews_list = self.client.get(f"/api/reviews/user/{tanvir['id']}").json()
        self.assertEqual(len(reviews_list), 1)
        self.assertEqual(reviews_list[0]["reviewer"]["name"], "Anik Sen")
        self.assertEqual(reviews_list[0]["rating"], 5)

    def test_scenario_2_overdue_coursebook_late_return_penalty(self):
        """Scenario 2: ME student lends book to CE student, returned past deadline, verifies -30 karma deduction."""
        # 1. Register Mehedi (ME, Batch 20) and Sakib (CE, Batch 22)
        mehedi, _, mehedi_h = self.register_and_login(
            name="Mehedi Hasan",
            email="mehedi2005042@stud.kuet.ac.bd",
        )
        sakib, _, sakib_h = self.register_and_login(
            name="Sakib Ahmed",
            email="sakib2201030@stud.kuet.ac.bd",
        )

        # 2. Mehedi lists Fluid Mechanics course textbook
        book = self.create_item(
            auth_headers=mehedi_h,
            title="Fluid Mechanics 9th Edition - Frank M. White",
            category="Books",
            specs="Hardcover, SI units, includes solved problems for ME/CE fluids",
            zone="me_bldg",
        )

        # 3. Sakib requests 4-hour loan
        req = self.create_borrow_request(
            auth_headers=sakib_h,
            item_id=book["id"],
            duration_hours=4,
            purpose="Mid-term exam preparation",
            pickup_zone="me_bldg",
        ).json()

        # 4. Mehedi accepts and starts handover
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=mehedi_h)
        start = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=mehedi_h).json()
        self.client.post("/api/transactions/verify", json_data={"request_id": req["id"], "otp": start["otp"]}, headers=sakib_h)

        # 5. Simulate 8 hours elapsed (past 4 hour duration)
        trans = self.db.query(models.Transaction).filter(models.Transaction.request_id == req["id"]).first()
        trans.borrowed_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=8)
        self.db.commit()

        # 6. Sakib confirms return overdue
        ret_resp = self.client.post(f"/api/transactions/return/{req['id']}", headers=sakib_h)
        self.assertEqual(ret_resp.status_code, 200)
        karma_data = ret_resp.json()["karma_updated"]
        self.assertFalse(karma_data["is_on_time"])
        self.assertEqual(karma_data["owner_gain"], 10)
        self.assertEqual(karma_data["borrower_change"], -30)

        # 7. Audit profiles
        sakib_prof = self.client.get("/api/auth/me", headers=sakib_h).json()
        self.assertEqual(sakib_prof["karma"], 70)
        self.assertEqual(sakib_prof["trust_score"], 70.0)
        self.assertEqual(sakib_prof["total_borrows"], 1)

        mehedi_prof = self.client.get("/api/auth/me", headers=mehedi_h).json()
        self.assertEqual(mehedi_prof["karma"], 110)
        self.assertEqual(mehedi_prof["trust_score"], 110.0)
        self.assertEqual(mehedi_prof["total_lends"], 1)

    def test_scenario_3_high_demand_beacon_and_competing_requests(self):
        """Scenario 3: High-demand item receives competing requests; owner accept resolves race condition cleanly."""
        # 1. Register Farhan (BME 23), Rifat (CSE 21), and Nabil (ECE 22)
        farhan, _, farhan_h = self.register_and_login(name="Farhan Kabir", email="farhan2315005@stud.kuet.ac.bd")
        rifat, _, rifat_h = self.register_and_login(name="Rifat Rahman", email="rifat2107050@stud.kuet.ac.bd")
        nabil, _, nabil_h = self.register_and_login(name="Nabil Islam", email="nabil2209022@stud.kuet.ac.bd")

        # 2. Farhan lists high-demand ECG sensor bundle
        sensor = self.create_item(
            auth_headers=farhan_h,
            title="AD8232 Heart Rate & ECG Monitor Sensor Kit",
            category="Lab Equipment",
            specs="Includes lead cables, electrodes, and 3.3V analog output",
            zone="central_library",
        )

        # 3. Both Rifat and Nabil submit borrow requests
        req_rifat = self.create_borrow_request(auth_headers=rifat_h, item_id=sensor["id"], message="Term project urgent").json()
        req_nabil = self.create_borrow_request(auth_headers=nabil_h, item_id=sensor["id"], message="Hardware defense").json()

        # 4. Farhan reviews and accepts Rifat
        self.client.put(f"/api/requests/{req_rifat['id']}/status", json_data={"status": "accepted"}, headers=farhan_h)

        # 5. Verify Nabil's request is automatically declined
        nabil_reqs = self.client.get("/api/requests/me", headers=nabil_h).json()
        nabil_status = [r["status"] for r in nabil_reqs if r["id"] == req_nabil["id"]][0]
        self.assertEqual(nabil_status, "declined")

        # 6. Verify item availability flag is False
        item_check = self.client.get(f"/api/items/{sensor['id']}").json()
        self.assertFalse(item_check["is_available"])

        # 7. Farhan cannot accidentally accept Nabil's declined request
        invalid_acc = self.client.put(
            f"/api/requests/{req_nabil['id']}/status",
            json_data={"status": "accepted"},
            headers=farhan_h,
        )
        self.assertEqual(invalid_acc.status_code, 400)

    def test_scenario_4_end_to_end_student_discovery_journey(self):
        """Scenario 4: Student discovers item via landmarks & search, initiates 1:1 chat, and completes exchange."""
        # 1. Setup senior and sophomore students
        senior, _, senior_h = self.register_and_login(name="Senior Student", email="senior2107099@stud.kuet.ac.bd")
        sophomore, _, sophomore_h = self.register_and_login(name="Sophomore Student", email="sophomore2307077@stud.kuet.ac.bd")

        # 2. Senior posts development board located at CSE building
        item = self.create_item(
            auth_headers=senior_h,
            title="Arduino Uno R3 Microcontroller Board",
            category="Electronics",
            specs="ATmega328P processor, 16MHz clock, includes USB cable",
            zone="cse_bldg",
            latitude=22.9003,
            longitude=89.5024,
        )

        # 3. Sophomore checks campus landmarks, verifies CSE building coordinates
        landmarks = self.client.get("/api/landmarks").json()
        cse_zone = [z for z in landmarks["zones"] if z["id"] == "cse_bldg"][0]
        self.assertEqual(cse_zone["coords"], [22.9003, 89.5024])

        # 4. Sophomore searches by processor keyword "ATmega328P"
        results = self.client.get("/api/items", params={"search": "ATmega328P"}).json()
        self.assertGreaterEqual(len(results), 1)

        # 5. Sophomore initiates direct 1:1 chat to coordinate pickup
        chat_msg = self.client.post(
            f"/api/chat/direct/{senior['id']}",
            json_data={"content": "Hi! Can we meet at the CSE ground floor lobby?", "item_id": item["id"]},
            headers=sophomore_h,
        )
        self.assertEqual(chat_msg.status_code, 200)

        # Senior replies
        self.client.post(
            f"/api/chat/direct/{sophomore['id']}",
            json_data={"content": "Sure, I am here right now!"},
            headers=senior_h,
        )

        # 6. Formal borrow request & OTP verification
        req = self.create_borrow_request(auth_headers=sophomore_h, item_id=item["id"]).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=senior_h)
        start = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=senior_h).json()
        verify = self.client.post("/api/transactions/verify", json_data={"request_id": req["id"], "otp": start["otp"]}, headers=sophomore_h)
        self.assertEqual(verify.status_code, 200)

        # Confirm borrowed state
        trans = self.db.query(models.Transaction).filter(models.Transaction.request_id == req["id"]).first()
        self.assertEqual(trans.status, "borrowed")

    def test_scenario_5_defective_item_reporting_and_safety_audit(self):
        """Scenario 5: Hazardous/defective equipment reported with specific safety reason and recorded in audit."""
        # 1. Register poster and reporter
        poster, _, poster_h = self.register_and_login(name="Poster", email="poster2107088@stud.kuet.ac.bd")
        reporter, _, reporter_h = self.register_and_login(name="Safety Vigilant", email="vigilant2307012@stud.kuet.ac.bd")

        # 2. Hazardous item posted
        hazardous_item = self.create_item(
            auth_headers=poster_h,
            title="High Voltage Power Supply 30V 5A",
            category="Lab Equipment",
            specs="Frayed power cable, ungrounded metal chassis",
        )

        # 3. Reporter flags item
        report_payload = {
            "reason": "Defective or Broken Item",
            "details": "Exposed copper wire on 220V AC input cord poses immediate electric shock and fire risk.",
        }
        report_resp = self.client.post(
            f"/api/items/{hazardous_item['id']}/report",
            json_data=report_payload,
            headers=reporter_h,
        )
        self.assertEqual(report_resp.status_code, 200)
        report_data = report_resp.json()
        self.assertIsNotNone(report_data["id"])
        self.assertEqual(report_data["item_id"], hazardous_item["id"])
        self.assertEqual(report_data["reason"], "Defective or Broken Item")

        # 4. Database audit verification
        report_in_db = self.db.query(models.Report).filter(models.Report.id == report_data["id"]).first()
        self.assertIsNotNone(report_in_db)
        self.assertEqual(report_in_db.reporter_id, reporter["id"])
        self.assertIn("shock", report_in_db.details.lower())
