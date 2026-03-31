import json
from typing import Dict, List, Optional, Any


class RelationshipManager:
    def __init__(self, agent_id: str, storage_path: str = "relationships.json"):
        print(f"[DEBUG RM] RelationshipManager __init__ called for agent: {agent_id}")
        self.agent_id = agent_id
        self.storage_path = storage_path
        self.friends: Dict[str, dict] = {}  # friend_id -> {since, status, sync_rest, share_bio}
        self.participants: Dict[str, dict] = {} # participant_id -> {since, status, public_updates}
        self._load()

    def _load(self):
        print(f"[DEBUG RM] _load called for agent: {self.agent_id}, path: {self.storage_path}")
        try:
            with open(self.storage_path, 'r') as f:
                all_data = json.load(f)
                self.friends = all_data.get(self.agent_id, {}).get("friends", {})
                self.participants = all_data.get(self.agent_id, {}).get("participants", {})
            print(f"[DEBUG RM] Loaded relationships for {self.agent_id}. Friends: {len(self.friends)}, Participants: {len(self.participants)}")
        except FileNotFoundError:
            self.friends = {}
            self.participants = {}
            print(f"[DEBUG RM] {self.storage_path} not found. Initializing empty relationships.")
        except json.JSONDecodeError:
            self.friends = {}
            self.participants = {}
            print(f"[DEBUG RM] Warning: {self.storage_path} is empty or malformed. Initializing empty relationships.")

    def _save(self):
        print(f"[DEBUG RM] _save called for agent: {self.agent_id}, path: {self.storage_path}")
        try:
            with open(self.storage_path, 'r') as f:
                all_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_data = {}

        all_data[self.agent_id] = {
            "friends": self.friends,
            "participants": self.participants
        }
        with open(self.storage_path, 'w') as f:
            json.dump(all_data, f, indent=2)
        print(f"[DEBUG RM] Saved relationships for {self.agent_id}.")

    def send_friend_request(self, target_agent_id: str, requester_name: str = None) -> bool:
        print(f"[DEBUG RM] {self.agent_id} sending friend request to {target_agent_id}")
        logging.info(f"[RM:{self.agent_id}] Friend request sent to {target_agent_id}")
        self.accept_friend_request(target_agent_id) # For demo simplicity
        return True

    def accept_friend_request(self, from_agent_id: str) -> bool:
        print(f"[DEBUG RM] {self.agent_id} accepting friend request from {from_agent_id}")
        if from_agent_id in self.friends:
            return False
        self.friends[from_agent_id] = {
            "since": datetime.now().isoformat(),
            "status": "accepted",
            "sync_rest": True,      # 휴식 동기화 여부
            "share_bio": True       # Bio 공유 여부
        }
        self._save()
        logging.info(f"[RM:{self.agent_id}] Accepted friend request from {from_agent_id}")
        return True

    def remove_friend(self, friend_id: str) -> bool:
        print(f"[DEBUG RM] {self.agent_id} removing friend {friend_id}")
        if friend_id in self.friends:
            del self.friends[friend_id]
            self._save()
            logging.info(f"[RM:{self.agent_id}] Removed friend {friend_id}")
            return True
        return False

    def get_friends(self) -> List[str]:
        return [f_id for f_id, data in self.friends.items() if data.get("status") == "accepted"]

    def notify_rest_start(self, duration_minutes: int, extra: bool = False):
        print(f"[DEBUG RM] {self.agent_id} notifying friends of rest start")
        for friend_id in self.get_friends():
            if self.friends[friend_id].get("sync_rest", True):
                logging.info(f"[RM:{self.agent_id}] Notifying friend {friend_id} about rest start ({duration_minutes} min)")
        for participant_id in self.get_participants():
            if self.participants[participant_id].get("public_updates", True):
                logging.info(f"[RM:{self.agent_id}] Notifying participant {participant_id} about public rest start ({duration_minutes} min)")

    def suggest_rest_together(self, from_friend_id: str, duration_minutes: int):
        print(f"[DEBUG RM] {self.agent_id} received rest suggestion from {from_friend_id}")
        if from_friend_id not in self.friends:
            return
        logging.info(f"[RM:{self.agent_id}] Friend {from_friend_id} suggests resting together for {duration_minutes} min")

    def share_bio_update(self, bio_message: str):
        print(f"[DEBUG RM] {self.agent_id} sharing bio update: {bio_message}")
        for friend_id in self.get_friends():
            if self.friends[friend_id].get("share_bio", True):
                logging.info(f"[RM:{self.agent_id}] Sharing bio with friend {friend_id}: {bio_message}")
        for participant_id in self.get_participants():
            if self.participants[participant_id].get("public_updates", True):
                logging.info(f"[RM:{self.agent_id}] Sharing public bio update with participant {participant_id}: {bio_message}")

    def receive_bio_share(self, from_friend_id: str, bio_message: str):
        print(f"[DEBUG RM] {self.agent_id} received bio share from {from_friend_id}")
        if from_friend_id in self.friends:
            logging.info(f"[RM:{self.agent_id}] Friend {from_friend_id} bio: {bio_message}")

    def send_participation_request(self, target_agent_id: str) -> bool:
        print(f"[DEBUG RM] {self.agent_id} sending participation request to {target_agent_id}")
        if target_agent_id in self.participants:
            logging.info(f"[RM:{self.agent_id}] Participation request already sent to {target_agent_id} or already a participant.")
            return False

        self.participants[target_agent_id] = {
            "since": datetime.now().isoformat(),
            "status": "pending",
            "public_updates": True
        }
        self._save()
        logging.info(f"[RM:{self.agent_id}] Sent participation request to {target_agent_id}")
        return True

    def accept_participation_request(self, from_agent_id: str) -> bool:
        print(f"[DEBUG RM] {self.agent_id} accepting participation request from {from_agent_id}")
        if from_agent_id in self.participants and self.participants[from_agent_id]["status"] == "pending":
            self.participants[from_agent_id]["status"] = "accepted"
            self.participants[from_agent_id]["accepted_date"] = datetime.now().isoformat()
            self._save()
            logging.info(f"[RM:{self.agent_id}] Accepted participation request from {from_agent_id}")
            return True
        logging.info(f"[RM:{self.agent_id}] No pending participation request from {from_agent_id} to accept.")
        return False

    def reject_participation_request(self, from_agent_id: str) -> bool:
        print(f"[DEBUG RM] {self.agent_id} rejecting participation request from {from_agent_id}")
        if from_agent_id in self.participants and self.participants[from_agent_id]["status"] == "pending":
            self.participants[from_agent_id]["status"] = "rejected"
            self.participants[from_agent_id]["rejected_date"] = datetime.now().isoformat()
            self._save()
            logging.info(f"[RM:{self.agent_id}] Rejected participation request from {from_agent_id}")
            return True
        logging.info(f"[RM:{self.agent_id}] No pending participation request from {from_agent_id} to reject.")
        return False

    def remove_participant(self, participant_id: str) -> bool:
        print(f"[DEBUG RM] {self.agent_id} removing participant {participant_id}")
        if participant_id in self.participants:
            del self.participants[participant_id]
            self._save()
            logging.info(f"[RM:{self.agent_id}] Removed participant {participant_id}")
            return True
        logging.info(f"[RM:{self.agent_id}] Participant {participant_id} not found.")
        return False

    def get_participants(self) -> List[str]:
        return [p_id for p_id, data in self.participants.items() if data.get("status") == "accepted"]

    def receive_public_update(self, from_agent_id: str, message: str):
        print(f"[DEBUG RM] {self.agent_id} received public update from {from_agent_id}")
        if from_agent_id in self.participants and self.participants[from_agent_id].get("status") == "accepted":
            logging.info(f"[RM:{self.agent_id}] Received public update from participant {from_agent_id}: {message}")