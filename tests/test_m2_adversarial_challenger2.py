"""
Milestone 2 Empirical Adversarial Test Suite
KUET CampusShare: Rigorous Challenge Harness by Challenger 2

Stress-tests:
1. Chat Messaging:
   - Self-chat rejection (HTTP 400)
   - Empty, whitespace, newline, and malformed message rejection
   - Unread counter tracking across single & multiple peers and bidirectional replies
   - Third-party unauthorized snooping on private request messages
2. Notifications:
   - Automated triggers on direct chat messages & request messages (recipient only)
   - Automated triggers on peer reviews (reviewee only)
   - Read status toggles, idempotency, and cross-user authorization isolation
   - Bulk mark-all-read isolation between distinct student accounts
3. Reviews and Reporting:
   - Self-review guard (HTTP 400)
   - 1-5 star bounds (rejecting <1, >5, negative, excessive, non-numeric)
   - Valid 1-5 rating spectrum persistence and retrieval
   - Moderation report submission on active items and 404 rejection on non-existent items
4. Items API & Campus Perimeter Geofencing:
   - KUET campus center [22.9006, 89.5024] and 700m perimeter validation
   - Haversine geofence calculations inside (<700m) and outside (>700m) campus
   - Coordinate field normalization (latitude/longitude, lat/lng, coords [lng, lat])
   - Type validation strictly accepting 'lend' and 'borrow', rejecting invalid types (rent, sell, buy, empty)
   - Filtering items by type and campus zone
"""

import math
import unittest
from tests.base import BaseE2ETestCase
from app import models


def haversine_distance(coord1, coord2):
    """Calculates haversine distance in meters between two [lat, lng] pairs."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class TestM2ChatAdversarial(BaseE2ETestCase):
    """Adversarial stress tests for chat messaging, input validation, and unread counters."""

    def test_01_self_chat_direct_rejected(self):
        """Student attempting direct chat with themselves is rejected with HTTP 400."""
        user, _, headers = self.register_and_login(name="Student Self", email="selfchat2107001@stud.kuet.ac.bd")
        resp = self.client.post(
            f"/api/chat/direct/{user['id']}",
            json_data={"content": "Talking to myself"},
            headers=headers,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("cannot chat with yourself", resp.json()["detail"].lower())

    def test_02_empty_message_direct_rejected(self):
        """Sending empty string direct message is rejected with HTTP 400."""
        user_a, _, _ = self.register_and_login(name="Student A", email="studanta2107002@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Student B", email="studantb2307003@stud.kuet.ac.bd")

        resp = self.client.post(
            f"/api/chat/direct/{user_a['id']}",
            json_data={"content": ""},
            headers=headers_b,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("message cannot be empty", resp.json()["detail"].lower())

    def test_03_whitespace_message_direct_rejected(self):
        """Sending whitespace-only direct message is rejected with HTTP 400."""
        user_a, _, _ = self.register_and_login(name="Student A", email="studanta2107004@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Student B", email="studantb2307005@stud.kuet.ac.bd")

        resp = self.client.post(
            f"/api/chat/direct/{user_a['id']}",
            json_data={"content": "     "},
            headers=headers_b,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("message cannot be empty", resp.json()["detail"].lower())

    def test_04_newlines_tabs_whitespace_direct_rejected(self):
        """Sending newlines, carriage returns, and tabs only is rejected with HTTP 400."""
        user_a, _, _ = self.register_and_login(name="Student A", email="studanta2107006@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Student B", email="studantb2307007@stud.kuet.ac.bd")

        resp = self.client.post(
            f"/api/chat/direct/{user_a['id']}",
            json_data={"content": "\n\t  \r\n \t"},
            headers=headers_b,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("message cannot be empty", resp.json()["detail"].lower())

    def test_05_empty_message_request_chat_rejected(self):
        """Sending empty message on request thread is rejected with HTTP 400."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107008@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Lab Board")
        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307009@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"]).json()

        resp = self.client.post(
            f"/api/chat/{req['id']}/messages",
            json_data={"content": "   "},
            headers=borrower_h,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("message cannot be empty", resp.json()["detail"].lower())

    def test_06_missing_content_field_rejected(self):
        """Payload without required 'content' field returns HTTP 422 Unprocessable Entity."""
        user_a, _, _ = self.register_and_login(name="Student A", email="studanta2107010@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Student B", email="studantb2307011@stud.kuet.ac.bd")

        resp = self.client.post(
            f"/api/chat/direct/{user_a['id']}",
            json_data={},
            headers=headers_b,
        )
        self.assertEqual(resp.status_code, 422)

    def test_07_chat_with_nonexistent_user_rejected(self):
        """Direct chat targeted at non-existent user returns HTTP 404."""
        _, _, headers = self.register_and_login(name="Student", email="student2107012@stud.kuet.ac.bd")
        resp = self.client.post(
            "/api/chat/direct/999999",
            json_data={"content": "Hello ghost"},
            headers=headers,
        )
        self.assertEqual(resp.status_code, 404)

    def test_08_unread_counter_tracking_single_peer(self):
        """Unread counter increments accurately per message and resets cleanly on reading."""
        user_a, _, headers_a = self.register_and_login(name="Student A", email="studanta2107013@stud.kuet.ac.bd")
        user_b, _, headers_b = self.register_and_login(name="Student B", email="studantb2307014@stud.kuet.ac.bd")

        # Initial: no conversations
        convs_b = self.client.get("/api/chat/conversations", headers=headers_b).json()
        self.assertEqual(len(convs_b), 0)

        # Student A sends 3 consecutive messages to Student B
        for i in range(1, 4):
            self.client.post(
                f"/api/chat/direct/{user_b['id']}",
                json_data={"content": f"Message number {i}"},
                headers=headers_a,
            )

        # Student B checks conversations: unread_count must be exactly 3
        convs_b = self.client.get("/api/chat/conversations", headers=headers_b).json()
        self.assertEqual(len(convs_b), 1)
        self.assertEqual(convs_b[0]["unread_count"], 3)
        self.assertEqual(convs_b[0]["last_message"], "Message number 3")
        self.assertEqual(convs_b[0]["contact"]["id"], user_a["id"])

        # Student A checks conversations: unread_count for A must be 0 (A was sender)
        convs_a = self.client.get("/api/chat/conversations", headers=headers_a).json()
        self.assertEqual(len(convs_a), 1)
        self.assertEqual(convs_a[0]["unread_count"], 0)

        # Student B reads messages from Student A
        read_resp = self.client.get(f"/api/chat/direct/{user_a['id']}", headers=headers_b)
        self.assertEqual(read_resp.status_code, 200)
        msgs = read_resp.json()
        self.assertEqual(len(msgs), 3)
        self.assertTrue(all(m["is_read"] for m in msgs))

        # Student B checks conversations again: unread_count must now be 0
        convs_b_after = self.client.get("/api/chat/conversations", headers=headers_b).json()
        self.assertEqual(convs_b_after[0]["unread_count"], 0)

    def test_09_unread_counter_multiple_peers_independent(self):
        """Unread counters for different peers operate completely independently."""
        user_a, _, headers_a = self.register_and_login(name="Peer A", email="peera2107015@stud.kuet.ac.bd")
        user_b, _, headers_b = self.register_and_login(name="Target B", email="targetb2107016@stud.kuet.ac.bd")
        user_c, _, headers_c = self.register_and_login(name="Peer C", email="peerc2307017@stud.kuet.ac.bd")

        # Peer A sends 2 messages to B
        for i in range(2):
            self.client.post(f"/api/chat/direct/{user_b['id']}", json_data={"content": f"A msg {i}"}, headers=headers_a)

        # Peer C sends 4 messages to B
        for i in range(4):
            self.client.post(f"/api/chat/direct/{user_b['id']}", json_data={"content": f"C msg {i}"}, headers=headers_c)

        # B views conversations: A should have 2 unread, C should have 4 unread
        convs = self.client.get("/api/chat/conversations", headers=headers_b).json()
        self.assertEqual(len(convs), 2)
        conv_map = {c["contact"]["id"]: c["unread_count"] for c in convs}
        self.assertEqual(conv_map[user_a["id"]], 2)
        self.assertEqual(conv_map[user_c["id"]], 4)

        # B reads only Peer A's messages
        self.client.get(f"/api/chat/direct/{user_a['id']}", headers=headers_b)

        # Verify: A unread is 0, C unread remains 4
        convs_updated = self.client.get("/api/chat/conversations", headers=headers_b).json()
        conv_map_updated = {c["contact"]["id"]: c["unread_count"] for c in convs_updated}
        self.assertEqual(conv_map_updated[user_a["id"]], 0)
        self.assertEqual(conv_map_updated[user_c["id"]], 4)

    def test_10_unread_counter_bidirectional_replies(self):
        """Outgoing replies do not inflate sender's unread counter but correctly increment peer's counter."""
        user_a, _, headers_a = self.register_and_login(name="Student A", email="studanta2107018@stud.kuet.ac.bd")
        user_b, _, headers_b = self.register_and_login(name="Student B", email="studantb2307019@stud.kuet.ac.bd")

        # A sends 2 messages to B
        self.client.post(f"/api/chat/direct/{user_b['id']}", json_data={"content": "Hi B 1"}, headers=headers_a)
        self.client.post(f"/api/chat/direct/{user_b['id']}", json_data={"content": "Hi B 2"}, headers=headers_a)

        # B replies to A without reading direct chat first
        self.client.post(f"/api/chat/direct/{user_a['id']}", json_data={"content": "Reply from B"}, headers=headers_b)

        # Check B's conversations: still has 2 unread from A (reply didn't mark A's incoming messages read)
        convs_b = self.client.get("/api/chat/conversations", headers=headers_b).json()
        self.assertEqual(convs_b[0]["unread_count"], 2)

        # Check A's conversations: has 1 unread from B
        convs_a = self.client.get("/api/chat/conversations", headers=headers_a).json()
        self.assertEqual(convs_a[0]["unread_count"], 1)

    def test_11_request_linked_chat_unauthorized_snooping(self):
        """Third party student cannot view or participate in private request chat."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107020@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Private Device")
        _, _, borrower_h = self.register_and_login(name="Borrower", email="borrower2307021@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"]).json()

        # Snoop student tries to access
        _, _, snoop_h = self.register_and_login(name="Snoop", email="snoop2307022@stud.kuet.ac.bd")
        get_res = self.client.get(f"/api/chat/{req['id']}/messages", headers=snoop_h)
        self.assertEqual(get_res.status_code, 403)

        post_res = self.client.post(
            f"/api/chat/{req['id']}/messages",
            json_data={"content": "I am spying"},
            headers=snoop_h,
        )
        self.assertEqual(post_res.status_code, 403)


class TestM2NotificationsAdversarial(BaseE2ETestCase):
    """Adversarial stress tests for automated notification triggers and status toggles."""

    def test_12_direct_message_triggers_recipient_notification_only(self):
        """Direct chat message sends notification to recipient, NOT sender."""
        user_a, _, headers_a = self.register_and_login(name="Sender Alice", email="alice2107030@stud.kuet.ac.bd")
        user_b, _, headers_b = self.register_and_login(name="Recipient Bob", email="bob2307031@stud.kuet.ac.bd")

        # Alice sends message to Bob
        resp = self.client.post(
            f"/api/chat/direct/{user_b['id']}",
            json_data={"content": "Meeting at Central Library"},
            headers=headers_a,
        )
        self.assertEqual(resp.status_code, 200)

        # Bob has 1 notification
        notifs_bob = self.client.get("/api/notifications", headers=headers_b).json()
        self.assertEqual(len(notifs_bob), 1)
        self.assertIn("Alice", notifs_bob[0]["title"])
        self.assertIn("Central Library", notifs_bob[0]["message"])
        self.assertEqual(notifs_bob[0]["link"], f"/chat?user={user_a['id']}")
        self.assertFalse(notifs_bob[0]["is_read"])

        # Alice has ZERO notifications
        notifs_alice = self.client.get("/api/notifications", headers=headers_a).json()
        self.assertEqual(len(notifs_alice), 0)

    def test_13_request_message_triggers_counterparty_notification_only(self):
        """Sending message on borrow request notifies the counterparty, not the sender."""
        user_owner, _, owner_h = self.register_and_login(name="Owner Owen", email="owen2107032@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Drafter")
        user_borrower, _, borrower_h = self.register_and_login(name="Borrower Ben", email="ben2307033@stud.kuet.ac.bd")
        req = self.create_borrow_request(auth_headers=borrower_h, item_id=item["id"]).json()

        # Borrower sends message to Owner
        resp = self.client.post(
            f"/api/chat/{req['id']}/messages",
            json_data={"content": "Can we meet at ME building?"},
            headers=borrower_h,
        )
        self.assertEqual(resp.status_code, 200)

        # Owner has notification
        notifs_owner = self.client.get("/api/notifications", headers=owner_h).json()
        self.assertEqual(len(notifs_owner), 1)
        self.assertIn(f"#{req['id']}", notifs_owner[0]["title"])
        self.assertEqual(notifs_owner[0]["link"], f"/chat/{req['id']}")

        # Borrower has zero notifications
        notifs_borrower = self.client.get("/api/notifications", headers=borrower_h).json()
        self.assertEqual(len(notifs_borrower), 0)

    def test_14_peer_review_triggers_reviewee_notification_only(self):
        """Submitting a peer review triggers notification for reviewee, not reviewer."""
        user_a, _, _ = self.register_and_login(name="Reviewee Ann", email="ann2107034@stud.kuet.ac.bd")
        user_b, _, headers_b = self.register_and_login(name="Reviewer Ben", email="ben2307035@stud.kuet.ac.bd")

        resp = self.client.post(
            "/api/reviews",
            json_data={
                "reviewee_id": user_a["id"],
                "rating": 5,
                "comment": "Super reliable lender on campus!",
            },
            headers=headers_b,
        )
        self.assertEqual(resp.status_code, 200)

        # Reviewee receives notification
        notifs_a = self.client.get("/api/notifications", headers=self.client.post(
            "/api/auth/login",
            json_data={"email": "ann2107034@stud.kuet.ac.bd", "password": "password123"}
        ).json()["access_token"]).json() if False else None  # helper below

        ann_h = {"Authorization": f"Bearer {self.login_user(email='ann2107034@stud.kuet.ac.bd').json()['access_token']}"}
        notifs_a = self.client.get("/api/notifications", headers=ann_h).json()
        self.assertEqual(len(notifs_a), 1)
        self.assertIn("5-star review", notifs_a[0]["title"])
        self.assertIn("Ben", notifs_a[0]["title"])
        self.assertIn("Super reliable", notifs_a[0]["message"])
        self.assertEqual(notifs_a[0]["link"], "/profile")

        # Reviewer receives zero notifications
        notifs_b = self.client.get("/api/notifications", headers=headers_b).json()
        self.assertEqual(len(notifs_b), 0)

    def test_15_notification_read_status_toggle_and_idempotency(self):
        """PUT /api/notifications/{id}/read marks as read and is idempotent."""
        user_a, _, headers_a = self.register_and_login(name="User A", email="notif2107036@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="User B", email="notif2307037@stud.kuet.ac.bd")

        self.client.post(f"/api/chat/direct/{user_a['id']}", json_data={"content": "Alert"}, headers=headers_b)
        notifs = self.client.get("/api/notifications", headers=headers_a).json()
        notif_id = notifs[0]["id"]
        self.assertFalse(notifs[0]["is_read"])

        # First toggle
        r1 = self.client.put(f"/api/notifications/{notif_id}/read", headers=headers_a)
        self.assertEqual(r1.status_code, 200)
        self.assertTrue(r1.json()["success"])

        # Check DB
        notifs_after = self.client.get("/api/notifications", headers=headers_a).json()
        self.assertTrue(notifs_after[0]["is_read"])

        # Second toggle (idempotent)
        r2 = self.client.put(f"/api/notifications/{notif_id}/read", headers=headers_a)
        self.assertEqual(r2.status_code, 200)

    def test_16_horizontal_privilege_escalation_mark_read(self):
        """Student cannot mark another student's notification as read (returns HTTP 404)."""
        user_a, _, headers_a = self.register_and_login(name="User A", email="priv2107038@stud.kuet.ac.bd")
        user_b, _, headers_b = self.register_and_login(name="User B", email="priv2307039@stud.kuet.ac.bd")
        _, _, headers_c = self.register_and_login(name="User C", email="priv2307040@stud.kuet.ac.bd")

        # Send notification to A
        self.client.post(f"/api/chat/direct/{user_a['id']}", json_data={"content": "Secret"}, headers=headers_c)
        notif_a_id = self.client.get("/api/notifications", headers=headers_a).json()[0]["id"]

        # Student B attempts to mark Student A's notification as read
        attack_resp = self.client.put(f"/api/notifications/{notif_a_id}/read", headers=headers_b)
        self.assertEqual(attack_resp.status_code, 404)

        # Student A's notification is still unread
        notifs_a = self.client.get("/api/notifications", headers=headers_a).json()
        self.assertFalse(notifs_a[0]["is_read"])

    def test_17_mark_all_read_isolation(self):
        """PUT /api/notifications/read-all affects only caller's notifications."""
        user_a, _, headers_a = self.register_and_login(name="User A", email="bulk2107041@stud.kuet.ac.bd")
        user_b, _, headers_b = self.register_and_login(name="User B", email="bulk2307042@stud.kuet.ac.bd")
        _, _, headers_c = self.register_and_login(name="User C", email="bulk2307043@stud.kuet.ac.bd")

        # 2 notifs for A
        self.client.post(f"/api/chat/direct/{user_a['id']}", json_data={"content": "Msg A1"}, headers=headers_c)
        self.client.post(f"/api/chat/direct/{user_a['id']}", json_data={"content": "Msg A2"}, headers=headers_c)

        # 2 notifs for B
        self.client.post(f"/api/chat/direct/{user_b['id']}", json_data={"content": "Msg B1"}, headers=headers_c)
        self.client.post(f"/api/chat/direct/{user_b['id']}", json_data={"content": "Msg B2"}, headers=headers_c)

        # A marks all read
        bulk_res = self.client.put("/api/notifications/read-all", headers=headers_a)
        self.assertEqual(bulk_res.status_code, 200)

        # A's notifications are all read
        notifs_a = self.client.get("/api/notifications", headers=headers_a).json()
        self.assertTrue(all(n["is_read"] for n in notifs_a))

        # B's notifications remain completely unread
        notifs_b = self.client.get("/api/notifications", headers=headers_b).json()
        self.assertTrue(all(not n["is_read"] for n in notifs_b))


class TestM2ReviewsAndReportingAdversarial(BaseE2ETestCase):
    """Adversarial stress tests for peer review guards, 1-5 rating bounds, and reporting."""

    def test_18_self_review_guard_rejected(self):
        """Attempting to submit review for oneself returns HTTP 400."""
        user, _, headers = self.register_and_login(name="Selfie", email="selfrev2107050@stud.kuet.ac.bd")
        resp = self.client.post(
            "/api/reviews",
            json_data={"reviewee_id": user["id"], "rating": 5, "comment": "Best student ever"},
            headers=headers,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("cannot review yourself", resp.json()["detail"].lower())

    def test_19_review_nonexistent_user_rejected(self):
        """Reviewing a non-existent student returns HTTP 404."""
        _, _, headers = self.register_and_login(name="Reviewer", email="revwho2107051@stud.kuet.ac.bd")
        resp = self.client.post(
            "/api/reviews",
            json_data={"reviewee_id": 999999, "rating": 4, "comment": "Ghost review"},
            headers=headers,
        )
        self.assertEqual(resp.status_code, 404)

    def test_20_rating_lower_bound_zero_rejected(self):
        """Rating of 0 is rejected by schema validator (HTTP 422 ge=1)."""
        user_a, _, _ = self.register_and_login(name="Target", email="target2107052@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Rater", email="rater2307053@stud.kuet.ac.bd")

        resp = self.client.post(
            "/api/reviews",
            json_data={"reviewee_id": user_a["id"], "rating": 0, "comment": "Zero stars"},
            headers=headers_b,
        )
        self.assertEqual(resp.status_code, 422)

    def test_21_rating_negative_rejected(self):
        """Negative rating is rejected by schema validator (HTTP 422)."""
        user_a, _, _ = self.register_and_login(name="Target", email="target2107054@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Rater", email="rater2307055@stud.kuet.ac.bd")

        resp = self.client.post(
            "/api/reviews",
            json_data={"reviewee_id": user_a["id"], "rating": -5, "comment": "Negative stars"},
            headers=headers_b,
        )
        self.assertEqual(resp.status_code, 422)

    def test_22_rating_upper_bound_six_rejected(self):
        """Rating of 6 is rejected by schema validator (HTTP 422 le=5)."""
        user_a, _, _ = self.register_and_login(name="Target", email="target2107056@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Rater", email="rater2307057@stud.kuet.ac.bd")

        resp = self.client.post(
            "/api/reviews",
            json_data={"reviewee_id": user_a["id"], "rating": 6, "comment": "Over the top"},
            headers=headers_b,
        )
        self.assertEqual(resp.status_code, 422)

    def test_23_rating_excessive_rejected(self):
        """Rating of 100 is rejected by schema validator (HTTP 422)."""
        user_a, _, _ = self.register_and_login(name="Target", email="target2107058@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Rater", email="rater2307059@stud.kuet.ac.bd")

        resp = self.client.post(
            "/api/reviews",
            json_data={"reviewee_id": user_a["id"], "rating": 100, "comment": "Super high"},
            headers=headers_b,
        )
        self.assertEqual(resp.status_code, 422)

    def test_24_rating_non_numeric_rejected(self):
        """Non-numeric string rating ('five') is rejected with HTTP 422."""
        user_a, _, _ = self.register_and_login(name="Target", email="target2107060@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Rater", email="rater2307061@stud.kuet.ac.bd")

        resp = self.client.post(
            "/api/reviews",
            json_data={"reviewee_id": user_a["id"], "rating": "five", "comment": "Word rating"},
            headers=headers_b,
        )
        self.assertEqual(resp.status_code, 422)

    def test_25_rating_valid_spectrum_1_to_5(self):
        """Every rating in the valid spectrum 1..5 is successfully accepted and stored."""
        user_a, _, _ = self.register_and_login(name="Target", email="target2107062@stud.kuet.ac.bd")
        _, _, headers_b = self.register_and_login(name="Rater", email="rater2307063@stud.kuet.ac.bd")

        for r in (1, 2, 3, 4, 5):
            resp = self.client.post(
                "/api/reviews",
                json_data={"reviewee_id": user_a["id"], "rating": r, "comment": f"Stars {r}"},
                headers=headers_b,
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()["rating"], r)

        # Retrieve user reviews list
        reviews = self.client.get(f"/api/reviews/user/{user_a['id']}").json()
        self.assertEqual(len(reviews), 5)

    def test_26_report_item_success(self):
        """Student can submit moderation report on an item with status pending."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107064@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Questionable Item")
        user_rep, _, rep_h = self.register_and_login(name="Reporter", email="rep2307065@stud.kuet.ac.bd")

        resp = self.client.post(
            f"/api/items/{item['id']}/report",
            json_data={
                "reason": "Safety hazard",
                "details": "Exposed high voltage wiring without isolation",
            },
            headers=rep_h,
        )
        self.assertEqual(resp.status_code, 200)
        report = resp.json()
        self.assertEqual(report["item_id"], item["id"])
        self.assertEqual(report["reporter_id"], user_rep["id"])
        self.assertEqual(report["reason"], "Safety hazard")
        self.assertEqual(report["status"], "pending")

    def test_27_report_nonexistent_item_rejected(self):
        """Reporting non-existent item returns HTTP 404."""
        _, _, rep_h = self.register_and_login(name="Reporter", email="rep2107066@stud.kuet.ac.bd")
        resp = self.client.post(
            "/api/items/999999/report",
            json_data={"reason": "Fake", "details": "Does not exist"},
            headers=rep_h,
        )
        self.assertEqual(resp.status_code, 404)

    def test_28_report_missing_reason_rejected(self):
        """Reporting item without reason field returns HTTP 422."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107067@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Valid Item")
        _, _, rep_h = self.register_and_login(name="Reporter", email="rep2307068@stud.kuet.ac.bd")

        resp = self.client.post(
            f"/api/items/{item['id']}/report",
            json_data={"details": "Missing reason field"},
            headers=rep_h,
        )
        self.assertEqual(resp.status_code, 422)

    def test_29_reporting_item_preserves_item_state(self):
        """Submitting a report does not modify item availability or delete the item."""
        _, _, owner_h = self.register_and_login(name="Owner", email="owner2107069@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=owner_h, title="Reported But Available")
        _, _, rep_h = self.register_and_login(name="Reporter", email="rep2307070@stud.kuet.ac.bd")

        self.client.post(
            f"/api/items/{item['id']}/report",
            json_data={"reason": "Spam", "details": "Listing text unclear"},
            headers=rep_h,
        )

        item_check = self.client.get(f"/api/items/{item['id']}").json()
        self.assertTrue(item_check["is_available"])
        self.assertEqual(item_check["title"], "Reported But Available")


class TestM2ItemsApiAndGeofenceAdversarial(BaseE2ETestCase):
    """Adversarial stress tests for items API, perimeter calculations, and type validation."""

    def test_30_kuet_campus_center_and_perimeter_definition(self):
        """Landmarks endpoint confirms official KUET center and 700m perimeter."""
        resp = self.client.get("/api/landmarks")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        campus = data["campus"]
        self.assertEqual(campus["center"], [22.9006, 89.5024])
        self.assertEqual(campus["boundary_radius_meters"], 700)

    def test_31_geofence_haversine_inside_perimeter(self):
        """Key campus landmark locations fall strictly within the 700m boundary."""
        center = [22.9006, 89.5024]
        campus_landmarks = [
            ("CSE Building", [22.9003, 89.5024], 33.3),
            ("EEE Building", [22.8998, 89.5031], 113.8),
            ("ME Building", [22.8990, 89.5032], 195.4),
            ("Civil Building", [22.8984, 89.5022], 245.5),
            ("Khan Jahan Ali Hall", [22.8950, 89.5000], 670.0),
            ("Teligati Mess Zone", [22.8948, 89.5009], 664.0),
        ]
        for name, coords, approx_expected in campus_landmarks:
            dist = haversine_distance(center, coords)
            self.assertLess(dist, 700.0, f"{name} {coords} distance {dist:.1f}m exceeds 700m boundary")

    def test_32_geofence_haversine_outside_perimeter(self):
        """Off-campus locations (>700m) are mathematically identified as outside the perimeter."""
        center = [22.9006, 89.5024]
        off_campus = [
            ("Khulna University Gollamari", [22.8023, 89.5332]),
            ("Khulna Railway Station", [22.8184, 89.5583]),
            ("Daulatpur Bus Stand", [22.8600, 89.5200]),
            ("Fulbarigate Crossing", [22.8900, 89.5150]),
        ]
        for name, coords in off_campus:
            dist = haversine_distance(center, coords)
            self.assertGreater(dist, 700.0, f"{name} {coords} unexpectedly inside 700m perimeter ({dist:.1f}m)")

    def test_33_coordinate_field_normalization(self):
        """Item creation accepts latitude/longitude or lat/lng and outputs synced fields."""
        _, _, headers = self.register_and_login(name="Geo Student", email="geo2107080@stud.kuet.ac.bd")

        # Test with latitude/longitude
        item1 = self.create_item(
            auth_headers=headers,
            title="Item LatLong",
            latitude=22.9003,
            longitude=89.5024,
        )
        self.assertEqual(item1["latitude"], 22.9003)
        self.assertEqual(item1["longitude"], 89.5024)
        self.assertEqual(item1["lat"], 22.9003)
        self.assertEqual(item1["lng"], 89.5024)
        self.assertEqual(item1["coords"], [89.5024, 22.9003])

        # Test with lat/lng in raw JSON payload
        resp2 = self.client.post(
            "/api/items",
            json_data={
                "title": "Item LatLng Alias",
                "category": "Electronics",
                "type": "lend",
                "lat": 22.8998,
                "lng": 89.5031,
                "zone": "eee_bldg",
            },
            headers=headers,
        )
        self.assertEqual(resp2.status_code, 201)
        item2 = resp2.json()["item"]
        self.assertEqual(item2["latitude"], 22.8998)
        self.assertEqual(item2["longitude"], 89.5031)
        self.assertEqual(item2["lat"], 22.8998)
        self.assertEqual(item2["lng"], 89.5031)
        self.assertEqual(item2["coords"], [89.5031, 22.8998])

    def test_34_item_creation_null_coordinates_handled(self):
        """Items without GPS coordinates are handled cleanly without error."""
        _, _, headers = self.register_and_login(name="Student", email="nullgeo2107081@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=headers, title="No GPS Item", latitude=None, longitude=None)
        self.assertIsNone(item["latitude"])
        self.assertIsNone(item["longitude"])
        self.assertIsNone(item["coords"])

    def test_35_item_type_lend_accepted_available_status(self):
        """Item type 'lend' is accepted and defaults status to 'available'."""
        _, _, headers = self.register_and_login(name="Lender", email="lend2107082@stud.kuet.ac.bd")
        item = self.create_item(auth_headers=headers, title="Lending Tool", item_type="lend")
        self.assertEqual(item["type"], "lend")
        self.assertEqual(item["status"], "available")
        self.assertTrue(item["is_available"])

    def test_36_item_type_borrow_accepted_beacon_status(self):
        """Item type 'borrow' is accepted and defaults status to 'beacon'."""
        _, _, headers = self.register_and_login(name="Borrower", email="beacon2107083@stud.kuet.ac.bd")
        resp = self.client.post(
            "/api/items",
            json_data={"title": "Need Graphing Calculator", "category": "Academic", "type": "borrow"},
            headers=headers,
        )
        self.assertEqual(resp.status_code, 201)
        item = resp.json()["item"]
        self.assertEqual(item["type"], "borrow")
        self.assertEqual(item["status"], "beacon")
        self.assertTrue(item["is_available"])

    def test_37_item_type_invalid_strings_rejected(self):
        """Item types not in ('lend', 'borrow') are rejected with HTTP 422."""
        _, _, headers = self.register_and_login(name="Student", email="invtype2107084@stud.kuet.ac.bd")

        invalid_types = ["rent", "buy", "sell", "giveaway", "exchange", ""]
        for bad_type in invalid_types:
            resp = self.client.post(
                "/api/items",
                json_data={"title": "Test Item", "category": "Other", "type": bad_type},
                headers=headers,
            )
            self.assertEqual(resp.status_code, 422, f"Failed to reject invalid type '{bad_type}'")
            self.assertIn("must be 'lend' or 'borrow'", resp.json()["detail"].lower())

    def test_38_item_filtering_by_type_lend_vs_borrow(self):
        """GET /api/items?type=... correctly partitions lend items from borrow beacons."""
        _, _, headers = self.register_and_login(name="Student", email="filter2107085@stud.kuet.ac.bd")

        # Create 2 lend items
        self.create_item(auth_headers=headers, title="Lend Item 1", item_type="lend")
        self.create_item(auth_headers=headers, title="Lend Item 2", item_type="lend")

        # Create 2 borrow beacons
        self.client.post("/api/items", json_data={"title": "Beacon 1", "type": "borrow"}, headers=headers)
        self.client.post("/api/items", json_data={"title": "Beacon 2", "type": "borrow"}, headers=headers)

        # Query lend only
        lend_res = self.client.get("/api/items", params={"type": "lend"}).json()
        self.assertTrue(len(lend_res) >= 2)
        self.assertTrue(all(item["type"] == "lend" for item in lend_res))

        # Query borrow only
        borrow_res = self.client.get("/api/items", params={"type": "borrow"}).json()
        self.assertTrue(len(borrow_res) >= 2)
        self.assertTrue(all(item["type"] == "borrow" for item in borrow_res))

        # Query all
        all_res = self.client.get("/api/items", params={"type": "ALL"}).json()
        types_found = {item["type"] for item in all_res}
        self.assertIn("lend", types_found)
        self.assertIn("borrow", types_found)

    def test_39_item_filtering_by_zone(self):
        """Querying items by zone isolates campus locations; non-existent zone returns empty list."""
        _, _, headers = self.register_and_login(name="Student", email="zone2107086@stud.kuet.ac.bd")

        self.create_item(auth_headers=headers, title="CSE Laptop Charger", zone="cse_bldg")
        self.create_item(auth_headers=headers, title="EEE Breadboard", zone="eee_bldg")

        cse_items = self.client.get("/api/items", params={"zone": "cse_bldg"}).json()
        self.assertTrue(all(i["zone"] == "cse_bldg" for i in cse_items))

        eee_items = self.client.get("/api/items", params={"zone": "eee_bldg"}).json()
        self.assertTrue(all(i["zone"] == "eee_bldg" for i in eee_items))

        ghost_items = self.client.get("/api/items", params={"zone": "nonexistent_zone"}).json()
        self.assertEqual(ghost_items, [])


if __name__ == "__main__":
    unittest.main()
