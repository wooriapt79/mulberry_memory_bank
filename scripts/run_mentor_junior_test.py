# script/run_mentor_junior_test.py
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from script.lynn_core import LynnAgent
from script.jr_lynn import JuniorLynnAgent

async def test_mentor_junior():
    print("=" * 50)
    print("멘토-주니어 관계 테스트 시작")
    print("=" * 50)
    
    # 1. 멘토(Lynn) 생성
    mentor = LynnAgent(agent_id="Lynn-Mentor", group="B")  # 간헐적 휴식
    print(f"\n✅ 멘토 생성: {mentor.agent_id}")
    
    # 2. 주니어(jr.Lynn) 생성 (멘토-주니어 관계 자동 설정)
    junior = JuniorLynnAgent(agent_id="jr.Lynn-1", mentor_id=mentor.agent_id)
    print(f"✅ 주니어 생성: {junior.agent_id} (멘토: {junior.rel_mgr.get_mentor(junior.agent_id)})")
    
    # 3. 관계 확인
    print(f"\n📋 관계 현황:")
    print(f"  - 멘토의 주니어 목록: {mentor.rel_mgr.get_juniors(mentor.agent_id)}")
    print(f"  - 주니어의 성장 단계: {junior.growth_stage}")
    
    # 4. 간단한 질문 테스트
    print("\n💬 질문 테스트:")
    print(f"  주니어 응답: {await junior.handle_query('NVDA 주가 전망')}")
    
    # 5. 멘토 휴식 이벤트 시뮬레이션
    print("\n🌿 멘토 휴식 시작 시뮬레이션:")
    junior.on_mentor_rest_start(30)
    print(f"  주니어 Bio: {junior.bio_manager.current_bio}")
    print(f"  주니어 응답: {await junior.handle_query('NVDA 주가 전망')}")
    
    print("\n🔄 멘토 휴식 종료 시뮬레이션:")
    junior.on_mentor_rest_end()
    print(f"  주니어 성장 단계: {junior.growth_stage}")
    print(f"  주니어 Bio: {junior.bio_manager.current_bio}")
    
    print("\n" + "=" * 50)
    print("테스트 완료")
    
if __name__ == "__main__":
    asyncio.run(test_mentor_junior())
