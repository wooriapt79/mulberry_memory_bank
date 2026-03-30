class RelationshipManager:
    def __init__(self, agent_id: str, storage_path: str = "relationships.json"):
        self.agent_id = agent_id
        self.storage_path = storage_path
        self.friends = {}

    def send_friend_request(self, target_agent_id: str):
        print(f"[RM:{self.agent_id}] Sending friend request to {target_agent_id}")

    def accept_friend_request(self, from_agent_id: str):
        print(f"[RM:{self.agent_id}] Accepting friend request from {from_agent_id}")
        self.friends[from_agent_id] = {'status': 'accepted'}

    def get_friends(self):
        return list(self.friends.keys())

    def notify_rest_start(self, duration_minutes: int, extra: bool = False):
        print(f"[RM:{self.agent_id}] Notifying friends of rest start for {duration_minutes} minutes.")

    def share_bio_update(self, bio_message: str):
        print(f"[RM:{self.agent_id}] Sharing bio update: {bio_message}")

