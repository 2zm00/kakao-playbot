import pyautogui
import pyperclip
import time
import sys
import re
import config

# === 설정 (CONFIG) ===
BOT_NAME = config.BOT_NAME  # "@플"
MY_USER_NAME = config.MY_USER_NAME  
DELAY = 0.5                 # 기본 입력 간격
WAIT_REPLY = float(config.WAIT_REPLY) # 봇 응답 대기 시간
TARGET_ENFORCE = int(config.TARGET_ENFORCE)
BASE_RARE = ["광선검", "핫도그", "칫솔", "주전자", "채찍", "꽃다발", "소시지", "새해 검"]

def clipboard_input(text):
    """클립보드를 이용한 한글 입력 (딜레이 보정)"""
    pyperclip.copy(text)
    time.sleep(0.1) 
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.1)

def send_mention_command(input_pos, command):
    """
    @플 -> 탭 -> (대기) -> 명령어 -> 엔터
    """
    pyautogui.click(input_pos)
    time.sleep(0.1)
    
    clipboard_input(BOT_NAME) 
    pyautogui.press('tab')
    clipboard_input(command)
    pyautogui.press('enter')
    time.sleep(WAIT_REPLY)

def get_last_chat_log(chat_region_pos):
    """채팅 내용을 긁어옵니다."""
    pyautogui.click(chat_region_pos)
    time.sleep(0.1)
    
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.1)
    
    return pyperclip.paste()

def parse_sell_result(text, target_list):
    """
    판매 결과에서 RARE 아이템 획득 여부 확인
    """
    if not text: return "NONE"
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines: return "NONE"
    
    # 마지막 10줄에서 검색
    search_range = range(max(0, len(lines)-10), len(lines))

    for idx in reversed(list(search_range)):
        line = lines[idx]
        if "획득:" in line and "[+0]" in line:
            match = re.search(r"\[\+0\]\s*([^\s(].*)", line)
            if not match and idx + 1 < len(lines):
                match = re.search(r"^([^\s(].*)", lines[idx + 1])
            
            if match:
                item_name = match.group(1).strip()
                item_name = re.split(r"[\(\[]", item_name)[0].strip()
                
                print(f"\n >> [감지] 획득 아이템: {item_name}")

                # target_list 는 main에서 설정한 필터
                is_target = any(target in item_name for target in target_list)

                if is_target:
                    print(f" >> [성공] 대상 아이템 확보: {item_name}")
                    return "TARGET_FOUND"
                else:
                    return "TRASH_ITEM"
    return "NONE"

def parse_reinforce_result(text, last_level):
    """
    강화 결과 분석
    """
    if not text: return "NONE", last_level
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines: return "NONE", last_level
    
    search_range = range(max(0, len(lines)-10), len(lines))

    for idx in reversed(list(search_range)):
        line = lines[idx]
        block_text = " ".join(lines[idx : idx + 3])

        if "골드가 부족해" in block_text :
            return "GOLD_SHORTAGE", last_level
        
        if "강화 성공" in block_text:
            # 패턴 1: +0 → +1
            match = re.search(r"→\s*\+(\d+)", block_text)
            # 패턴 2: [+1]
            if not match: match = re.search(r"\[\+(\d+)\]", block_text)
            if match: return "SUCCESS", int(match.group(1))

        if "강화 유지" in block_text or "레벨이 유지" in block_text:
            return "MAINTAIN", last_level
        
        if "강화 파괴" in block_text or "산산조각" in block_text:
            return "DESTROY", 0

    return "NONE", last_level

def main():
    print("=== 카카오톡 골드 수급 매크로 (무한 반복) ===")
    
    try:
        target_input = input(f">> 목표 강화 수치를 입력하세요 (기본 {TARGET_ENFORCE}): ").strip()
        target_enforce = int(target_input) if target_input else TARGET_ENFORCE
    except ValueError:
        target_enforce = TARGET_ENFORCE

    print("\n[필터 설정]")
    print(" 1: 모든 무기 강화 (검, 몽둥이 포함)")
    print(" 2: 레어 아이템만 강화 (검, 몽둥이는 즉시 판매)")
    choice = input(">> 선택 (1/2): ").strip()

    if choice == "2":
        target_list = BASE_RARE
        print("[*] 설정: 레어 아이템만 타겟으로 지정합니다.")
    else:
        target_list = BASE_RARE + ["검", "몽둥이", "뭉둥이"]
        print("[*] 설정: 모든 무기를 타겟으로 지정합니다.")

    print("\n[1단계] 마우스를 '채팅 입력창' 위에 올리세요.")
    input(">> 준비됐다면 Enter...")
    input_x, input_y = pyautogui.position()
    
    print("\n[2단계] 마우스를 '채팅 로그 영역' 위에 올리세요.")
    input(">> 준비됐다면 Enter...")
    chat_x, chat_y = pyautogui.position()
    
    print(f"\n[*] 동작 시작: 목표 +{target_enforce}강 / (중단: ESC 꾹 누르기)")
    time.sleep(3)

    pos_input = (input_x, input_y)
    pos_chat = (chat_x, chat_y)
    
    state = "ACQUIRE" # ACQUIRE or ENFORCE
    count = 1
    current_level = 0



    while True:
        if state == "ACQUIRE":
            print(f"\n[{count}회차] '판매' 전송 (아이템 찾는 중...)")
            # 초기 상태 확인을 위해 강화 한 번 시도 (아이템 유뮤 체크용)
            send_mention_command(pos_input, "강화")
            send_mention_command(pos_input, "판매")
            time.sleep(WAIT_REPLY)
            # 응답 대기 (최대 12초)
            for _ in range(12):
                log_text = get_last_chat_log(pos_chat)
                res = parse_sell_result(log_text, target_list)
                
                if res == "TARGET_FOUND":
                    print(" >> [발견] 대상 아이템 확보! 강화 단계 진입")
                    state = "ENFORCE"
                    current_level = 0
                    break # for 문만 탈출 -> while 문에 의해 다음 턴 진행
                elif res == "TRASH_ITEM":
                    print(" >> 불필요한 아이템입니다. 다음 판매를 위해 루프를 계속합니다.")
                    break # for 문만 탈출 -> while 문에 의해 다음 턴 진행
            else:
                # for 문이 break 없이 끝났을 때 (타임아웃)
                print(" >> 응답 없음. 다음 턴에서 다시 시도합니다.")

        elif state == "ENFORCE":
            print(f"\n[{count}회차] '강화' 전송 (현재: +{current_level} / 목표: +{target_enforce})")
            send_mention_command(pos_input, "강화")
            time.sleep(WAIT_REPLY)

            # 응답 대기 (최대 15초)
            for _ in range(15):
                log_text = get_last_chat_log(pos_chat)
                status, new_level = parse_reinforce_result(log_text, current_level)
                
                if status != "NONE":
                    print(f" >> 결과: [{status}] 수치: +{new_level}")
                    current_level = new_level
                    
                    if status == "DESTROY":
                        print(" >> [파괴] 다시 아이템을 찾으러 갑니다.")
                        state = "ACQUIRE"
                    elif status == "GOLD_SHORTAGE":
                        print(" >> [중단] 골드가 부족하여 종료합니다.")
                        return # 스크립트 완전 종료
                    elif current_level >= target_enforce:
                        print(f" >> [달성] +{current_level}강 도달! 판매하여 골드를 수급하고 재시작합니다.")
                        send_mention_command(pos_input, "판매")
                        time.sleep(WAIT_REPLY)
                        state = "ACQUIRE" # 판매 후 다시 아이템 찾기 단계로
                    
                    break # for 문만 탈출 -> while 문에 의해 다음 턴 진행
            else:
                # for 문이 break 없이 끝났을 때 (타임아웃)
                print(" >> 응답 없음. 다시 시도합니다.")

        count += 1
        time.sleep(1.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
