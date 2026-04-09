@@ -0,0 +1,152 @@
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

class RelationshipManager:
    """
    AI 에이전트 간 관계 관리자
    - 친구 관계 (Friend)
    - 멘토-주니어 관계 (Mentor-Junior)
    """
    def __init__(self, agent_id: str, storage_path: str = "relationships.json"):
        self.agent_id = agent_id
        self.storage_path = storage_path
        self.friends: Dict[str, dict] = {}          # friend_id -> {since, sync_rest, share_bio}
        self.mentor_of: Dict[str, str] = {}          # junior_id -> mentor_id
        self.junior_of: Dict[str, List[str]] = {}    # mentor_id -> list of junior_ids
        self._load()

    # ========== Private Methods ==========
    def _load(self):
        """파일에서 관계 데이터 로드"""
        try:
            with open(self.storage_path, 'r') as f:
                all_data = json.load(f)
                agent_data = all_data.get(self.agent_id, {})
                self.friends = agent_data.get("friends", {})
                self.mentor_of = agent_data.get("mentor_of", {})
                self.junior_of = agent_data.get("junior_of", {})
        except FileNotFoundError:
            pass

    def _save(self):
        """관계 데이터를 파일에 저장"""
        try:
            with open(self.storage_path, 'r') as f:
                all_data = json.load(f)
        except FileNotFoundError:
            all_data = {}
        all_data[self.agent_id] = {
            "friends": self.friends,
            "mentor_of": self.mentor_of,
            "junior_of": self.junior_of
        }
        with open(self.storage_path, 'w') as f:
            json.dump(all_data, f, indent=2)

    # ========== Friend Relationship Methods ==========
    def send_friend_request(self, target_agent_id: str) -> bool:
        """친구 요청 보내기 (실제로는 상대방의 accept 호출이 필요하나, 여기서는 직접 수락)"""
        logging.info(f"[RM:{self.agent_id}] Friend request sent to {target_agent_id}")
        # 실제 구현에서는 메시지 큐 등을 통해 요청 전달, 여기서는 즉시 수락 처리
        return self.accept_friend_request(target_agent_id)

    def accept_friend_request(self, from_agent_id: str) -> bool:
        """친구 요청 수락"""
        if from_agent_id in self.friends:
            return False
        self.friends[from_agent_id] = {
            "since": datetime.now().isoformat(),
            "sync_rest": True,
            "share_bio": True
        }
        self._save()
        logging.info(f"[RM:{self.agent_id}] Accepted friend request from {from_agent_id}")
        return True

    def remove_friend(self, friend_id: str) -> bool:
        """친구 삭제"""
        if friend_id in self.friends:
            del self.friends[friend_id]
            self._save()
            logging.info(f"[RM:{self.agent_id}] Removed friend {friend_id}")
            return True
        return False

    def get_friends(self) -> List[str]:
        """친구 목록 반환"""
        return list(self.friends.keys())

    def notify_rest_start(self, duration_minutes: int, extra: bool = False):
        """내가 휴식 시작 → 친구들에게 알림 (휴식 동기화)"""
        for friend_id in self.get_friends():
            if self.friends[friend_id].get("sync_rest", True):
                logging.info(f"[RM:{self.agent_id}] Notifying friend {friend_id} about rest start ({duration_minutes} min)")
                # 실제 구현: 상대방의 suggest_rest_together() 호출

    def share_bio_update(self, bio_message: str):
        """내 Bio 변경 → 친구들에게 공유"""
        for friend_id in self.get_friends():
            if self.friends[friend_id].get("share_bio", True):
                logging.info(f"[RM:{self.agent_id}] Sharing bio with friend {friend_id}: {bio_message}")

    # ========== Mentor-Junior Relationship Methods ==========
    def add_mentor_relationship(self, mentor_id: str, junior_id: str) -> bool:
        """멘토-주니어 관계 설정 (멘토 입장에서 호출)"""
        if junior_id in self.mentor_of:
            logging.warning(f"[RM:{self.agent_id}] Junior {junior_id} already has mentor {self.mentor_of[junior_id]}")
            return False
        self.mentor_of[junior_id] = mentor_id
        if mentor_id not in self.junior_of:
            self.junior_of[mentor_id] = []
        if junior_id not in self.junior_of[mentor_id]:
            self.junior_of[mentor_id].append(junior_id)
        self._save()
        logging.info(f"[RM:{self.agent_id}] Mentor relationship added: {mentor_id} -> {junior_id}")
        return True

    def get_mentor(self, junior_id: str) -> Optional[str]:
        """주니어의 멘토 조회"""
        return self.mentor_of.get(junior_id)

    def get_juniors(self, mentor_id: str) -> List[str]:
        """멘토의 주니어 목록 조회"""
        return self.junior_of.get(mentor_id, [])

    def remove_mentor_relationship(self, junior_id: str) -> bool:
        """멘토-주니어 관계 해제"""
        if junior_id not in self.mentor_of:
            return False
        mentor_id = self.mentor_of[junior_id]
        del self.mentor_of[junior_id]
        if mentor_id in self.junior_of:
            self.junior_of[mentor_id] = [j for j in self.junior_of[mentor_id] if j != junior_id]
        self._save()
        logging.info(f"[RM:{self.agent_id}] Mentor relationship removed: {mentor_id} -> {junior_id}")
        return True

    def notify_mentor_rest(self, mentor_id: str, duration: int, extra: bool = False):
        """멘토가 휴식 시작 → 자신의 주니어들에게 알림"""
        for junior_id in self.get_juniors(mentor_id):
            logging.info(f"[RM:{self.agent_id}] Notifying junior {junior_id} that mentor {mentor_id} is resting ({duration} min)")
            # 실제 구현: 주니어 에이전트의 on_mentor_rest_start() 호출

    def get_mentor_status_summary(self, mentor_id: str) -> dict:
        """멘토의 주니어 현황 요약"""
        return {
            'mentor_id': mentor_id,
            'total_juniors': len(self.get_juniors(mentor_id)),
            'junior_ids': self.get_juniors(mentor_id),
            'has_mentor': mentor_id in self.mentor_of.values()
        }

# 간단한 테스트 코드 (모듈 단독 실행 시)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    rm = RelationshipManager("test_agent")
    rm.accept_friend_request("friend_A")
    rm.add_mentor_relationship("mentor_X", "junior_Y")
    print("Friends:", rm.get_friends())
    print("Juniors of mentor_X:", rm.get_juniors("mentor_X"))
    print("Mentor of junior_Y:", rm.get_mentor("junior_Y"))
