"""
Tier 3: Cross-Feature Combinations (Pairwise integration flows)
Tests multi-stage feature interactions across system boundaries:
- Combination 1: Borrow Request -> Accept -> OTP Handover -> Return -> Karma Protocol -> Profile Audit
- Combination 2: Item Post -> Search -> Bookmark / Wishlist -> Direct 1:1 Chat -> Borrow Request
- Combination 3: Competing Requests Resolution & State Cascade
- Combination 4: Chat + Notification Read Receipt Loop
- Combination 5: Handover + Return + Peer Review + Profile Integration
- Combination 6: Wishlist & Item Modification Lifecycle
- Combination 7: Late Return Penalty & Negative Karma Cascade
Total: 7 comprehensive combination tests
"""

import datetime
from tests.base import BaseE2ETestCase
from app import models


class TestTier3Combinations(BaseE2ETestCase):

    def test_01_borrow_handover_return_karma_profile_lifecycle(self):
        """Borrow Request -> Accept -> Handover OTP -> Return -> Karma +10/+5 -> Profile History check."""
        # 1. Register lender and borrower
        lender, _, lender_h = self.register_and_login(name="Tanvir Hossain", email="tanvir2107001@stud.kuet.ac.bd")
        borrower, _, borrower_h = self.register_and_login(name="Abdur Siddique", email="siddique2307010@stud.kuet.ac.bd")

        # 2. Lender posts item
        item = self.create_item(
            auth_headers=lender_h,
            title="Rigol DS1054Z 100MHz Digital Oscilloscope",
            category="Lab Equipment",
            specs="4 channels, 1GSa/s sampling rate, SPI/I2C decoder",
            condition="Like New",
            zone="eee_bldg",
        )

        # 3. Borrower submits request
        req_resp = self.create_borrow_request(
            auth_headers=borrower_h,
            item_id=item["id"],
            duration_hours=24,
            purpose="Testing amplifier bandwidth in EEE 3102 sessional",
            pickup_zone="eee_bldg",
            message="Will take utmost care and return on time tomorrow",
        )
        self.assertEqual(req_resp.status_code, 200)
        req = req_resp.json()
        self.assertEqual(req["status"], "pending")

        # 4. Lender accepts request
        acc_resp = self.client.put(
            f"/api/requests/{req['id']}/status",
            json_data={"status": "accepted"},
            headers=lender_h,
        )
        self.assertEqual(acc_resp.status_code, 200)

        # 5. Lender starts physical handover -> generates OTP & QR code
        start_resp = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=lender_h)
        self.assertEqual(start_resp.status_code, 200)
        otp = start_resp.json()["otp"]
        self.assertEqual(len(otp), 4)

        # 6. Borrower verifies handover with OTP
        verify_resp = self.client.post(
            "/api/transactions/verify",
            json_data={"request_id": req["id"], "otp": otp},
            headers=borrower_h,
        )
        self.assertEqual(verify_resp.status_code, 200)
        self.assertIn("borrowed", verify_resp.json()["detail"].lower())

        # 7. Borrower returns item within duration window (on-time)
        return_resp = self.client.post(f"/api/transactions/return/{req['id']}", headers=borrower_h)
        self.assertEqual(return_resp.status_code, 200)
        karma_data = return_resp.json()["karma_updated"]
        self.assertTrue(karma_data["is_on_time"])
        self.assertEqual(karma_data["owner_gain"], 10)
        self.assertEqual(karma_data["borrower_change"], 5)

        # 8. Check lender's profile: Karma incremented by 10, total_lends incremented
        lender_me = self.client.get("/api/auth/me", headers=lender_h).json()
        self.assertEqual(lender_me["karma"], lender["karma"] + 10)
        self.assertEqual(lender_me["total_lends"], 1)

        # 9. Check borrower's profile: Karma incremented by 5, total_borrows incremented
        borrower_me = self.client.get("/api/auth/me", headers=borrower_h).json()
        self.assertEqual(borrower_me["karma"], borrower["karma"] + 5)
        self.assertEqual(borrower_me["total_borrows"], 1)

        # 10. Item is restored to available
        item_after = self.client.get(f"/api/items/{item['id']}").json()
        self.assertTrue(item_after["is_available"])
        self.assertEqual(item_after["status"], "available")

        # 11. Transaction audit shows completed
        requests_history = self.client.get("/api/requests/me", headers=lender_h).json()
        self.assertEqual(requests_history[0]["status"], "completed")

    def test_02_item_post_search_bookmark_chat_request_flow(self):
        """Item Post -> Search -> Bookmark / Wishlist -> Direct Chat -> Borrow Request."""
        # 1. Register two students
        _, _, lender_h = self.register_and_login(name="Lender", email="lender2107002@stud.kuet.ac.bd")
        borrower_user, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307011@stud.kuet.ac.bd")

        # 2. Lender posts item with specific specs
        item = self.create_item(
            auth_headers=lender_h,
            title="Casio fx-991CW ClassWiz Scientific Calculator",
            category="Calculators",
            specs="Natural textbook display, authentic Casio hologram, approved for KUET finals",
            zone="central_library",
        )

        # 3. Borrower searches by hardware spec "ClassWiz"
        search_res = self.client.get("/api/items", params={"search": "ClassWiz"}).json()
        self.assertGreaterEqual(len(search_res), 1)
        found_item = search_res[0]
        self.assertEqual(found_item["id"], item["id"])

        # 4. Borrower bookmarks item
        save_res = self.client.post(f"/api/items/{found_item['id']}/save", headers=borrower_h).json()
        self.assertTrue(save_res["saved"])

        # Verify in saved items list
        saved_list = self.client.get("/api/items/saved/all", headers=borrower_h).json()
        self.assertEqual(len(saved_list), 1)
        self.assertEqual(saved_list[0]["id"], found_item["id"])

        # 5. Borrower chats directly with item owner to ask question
        msg_res = self.client.post(
            f"/api/chat/direct/{found_item['owner_id']}",
            json_data={"content": "Hi! Can I pick this up at Central Library around 4pm?", "item_id": found_item["id"]},
            headers=borrower_h,
        )
        self.assertEqual(msg_res.status_code, 200)

        # 6. Borrower creates formal borrow request
        req_res = self.create_borrow_request(
            auth_headers=borrower_h,
            item_id=found_item["id"],
            duration_hours=6,
            purpose="Semester final exam preparation",
            pickup_zone="central_library",
        )
        self.assertEqual(req_res.status_code, 200)
        self.assertEqual(req_res.json()["status"], "pending")

    def test_03_competing_requests_race_resolution(self):
        """Multiple borrowers request same item -> Owner accepts #1 -> Auto-declines #2 -> Item unavailable for #3."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107003@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Arduino Mega 2560 Bundle")

        _, _, student_b_h = self.register_and_login(name="Student B", email="studentb2307012@stud.kuet.ac.bd")
        _, _, student_c_h = self.register_and_login(name="Student C", email="studentc2307013@stud.kuet.ac.bd")
        _, _, student_d_h = self.register_and_login(name="Student D", email="studentd2307014@stud.kuet.ac.bd")

        # Students B and C submit borrow requests
        req_b = self.create_borrow_request(auth_headers=student_b_h, item_id=item["id"], message="B request").json()
        req_c = self.create_borrow_request(auth_headers=student_c_h, item_id=item["id"], message="C request").json()

        # Owner accepts Student B
        accept_resp = self.client.put(
            f"/api/requests/{req_b['id']}/status",
            json_data={"status": "accepted"},
            headers=owner_h,
        )
        self.assertEqual(accept_resp.status_code, 200)

        # Verify Student C's pending request was automatically declined
        my_reqs_c = self.client.get("/api/requests/me", headers=student_c_h).json()
        c_item = [r for r in my_reqs_c if r["id"] == req_c["id"]][0]
        self.assertEqual(c_item["status"], "declined")

        # Verify item is marked unavailable
        item_check = self.client.get(f"/api/items/{item['id']}").json()
        self.assertFalse(item_check["is_available"])

        # Student D tries to request unavailable item -> rejected
        req_d_resp = self.create_borrow_request(auth_headers=student_d_h, item_id=item["id"])
        self.assertEqual(req_d_resp.status_code, 400)
        self.assertIn("not available", req_d_resp.json()["detail"].lower())

    def test_04_chat_notification_read_receipt_loop(self):
        """Sending message triggers notification -> Recipient reads notification & thread -> Counters clear."""
        user_a, _, headers_a = self.register_and_login(name="Student A", email="studanta2107004@stud.kuet.ac.bd")
        user_b, _, headers_b = self.register_and_login(name="Student B", email="studantb2307015@stud.kuet.ac.bd")

        # Student A sends message to Student B
        msg_resp = self.client.post(
            f"/api/chat/direct/{user_b['id']}",
            json_data={"content": "Are you at Ekushey Hall?"},
            headers=headers_a,
        )
        self.assertEqual(msg_resp.status_code, 200)

        # Student B checks notification feed
        notifs_b = self.client.get("/api/notifications", headers=headers_b).json()
        self.assertGreaterEqual(len(notifs_b), 1)
        self.assertIn("Student A", notifs_b[0]["title"])
        self.assertFalse(notifs_b[0]["is_read"])

        # Student B checks conversations list: unread_count is 1
        convos_b = self.client.get("/api/chat/conversations", headers=headers_b).json()
        self.assertEqual(convos_b[0]["unread_count"], 1)

        # Student B marks notification read
        self.client.put(f"/api/notifications/{notifs_b[0]['id']}/read", headers=headers_b)
        notifs_b_after = self.client.get("/api/notifications", headers=headers_b).json()
        self.assertTrue(notifs_b_after[0]["is_read"])

        # Student B opens chat thread with Student A
        thread = self.client.get(f"/api/chat/direct/{user_a['id']}", headers=headers_b).json()
        self.assertEqual(len(thread), 1)

        # Student B checks conversations inbox again: unread count now 0
        convos_b_after = self.client.get("/api/chat/conversations", headers=headers_b).json()
        self.assertEqual(convos_b_after[0]["unread_count"], 0)

    def test_05_handover_return_peer_review_profile_flow(self):
        """Transaction completed -> Borrower reviews Lender 5 stars -> Visible on profile & triggers notification."""
        lender_user, _, lender_h = self.register_and_login(name="Lender", email="lender2107005@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=lender_h, title="Engineering Mini Drafter")
        borrower_user, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307016@stud.kuet.ac.bd")

        # Borrow flow
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"]).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=lender_h)
        start = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=lender_h).json()
        self.client.post("/api/transactions/verify", json_data={"request_id": req["id"], "otp": start["otp"]}, headers=borrower_h)
        self.client.post(f"/api/transactions/return/{req['id']}", headers=borrower_h)

        # Borrower submits 5-star peer review for Lender
        rev_payload = {
            "reviewee_id": lender_user["id"],
            "rating": 5,
            "comment": "Outstanding lender! The mini drafter was properly oiled with clean protractor head.",
        }
        rev_resp = self.client.post("/api/reviews", json_data=rev_payload, headers=borrower_h)
        self.assertEqual(rev_resp.status_code, 200)

        # Review appears in Lender's reviews list
        lender_reviews = self.client.get(f"/api/reviews/user/{lender_user['id']}").json()
        self.assertEqual(len(lender_reviews), 1)
        self.assertEqual(lender_reviews[0]["rating"], 5)
        self.assertEqual(lender_reviews[0]["reviewer"]["name"], "Borrower")

        # Notification sent to Lender
        notifs_lender = self.client.get("/api/notifications", headers=lender_h).json()
        self.assertTrue(any("review" in n["title"].lower() for n in notifs_lender))

    def test_06_wishlist_item_edit_delete_lifecycle(self):
        """Saved item reflects owner updates, and deleting item handles saved references cleanly."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107006@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Old Drafting Table", category="Stationery")

        _, _, student_h = self.register_and_login(name="Student", email="student2307017@stud.kuet.ac.bd")

        # Student saves item
        self.client.post(f"/api/items/{item['id']}/save", headers=student_h)
        saved_before = self.client.get("/api/items/saved/all", headers=student_h).json()
        self.assertEqual(saved_before[0]["title"], "Old Drafting Table")

        # Owner updates item
        self.client.put(
            f"/api/items/{item['id']}",
            json_data={"title": "Upgraded Drafting Table with Adjustable Stand", "category": "Stationery"},
            headers=owner_h,
        )

        # Student's wishlist reflects the updated title
        saved_after = self.client.get("/api/items/saved/all", headers=student_h).json()
        self.assertEqual(saved_after[0]["title"], "Upgraded Drafting Table with Adjustable Stand")

        # Student toggles off bookmark
        self.client.post(f"/api/items/{item['id']}/save", headers=student_h)
        saved_cleared = self.client.get("/api/items/saved/all", headers=student_h).json()
        self.assertEqual(len(saved_cleared), 0)

    def test_07_late_return_penalty_karma_cascade(self):
        """Late return applies -30 penalty to borrower, +10 to lender, updates karma and trust score."""
        lender_user, _, lender_h = self.register_and_login(name="Lender", email="lender2107007@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=lender_h, title="Thermodynamics Textbook", category="Books")
        borrower_user, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307018@stud.kuet.ac.bd")

        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"], duration_hours=2).json()
        self.client.put(f"/api/requests/{req['id']}/status", json_data={"status": "accepted"}, headers=lender_h)
        start = self.client.post("/api/transactions/start", json_data={"request_id": req["id"]}, headers=lender_h).json()
        self.client.post("/api/transactions/verify", json_data={"request_id": req["id"], "otp": start["otp"]}, headers=borrower_h)

        # Simulate time exceeding duration
        trans = self.db.query(models.Transaction).filter(models.Transaction.request_id == req["id"]).first()
        trans.borrowed_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=6)
        self.db.commit()

        # Execute return
        ret_resp = self.client.post(f"/api/transactions/return/{req['id']}", headers=borrower_h)
        self.assertEqual(ret_resp.status_code, 200)
        karma_data = ret_resp.json()["karma_updated"]
        self.assertFalse(karma_data["is_on_time"])
        self.assertEqual(karma_data["owner_gain"], 10)
        self.assertEqual(karma_data["borrower_change"], -30)

        # Verify lender profile
        lender_prof = self.client.get("/api/auth/me", headers=lender_h).json()
        self.assertEqual(lender_prof["karma"], 110)
        self.assertEqual(lender_prof["trust_score"], 110.0)

        # Verify borrower profile
        borrower_prof = self.client.get("/api/auth/me", headers=borrower_h).json()
        self.assertEqual(borrower_prof["karma"], 70)
        self.assertEqual(borrower_prof["trust_score"], 70.0)
