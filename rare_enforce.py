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
RARE = ["광선검", "핫도그", "칫솔", "주전자", "채찍", "꽃다발", "소시지", "새해 검"]

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
    time.sleep(DELAY)
    
    pyautogui.press('tab')
    time.sleep(DELAY + 0.2) 
    
    clipboard_input(command)
    time.sleep(DELAY)
    
    pyautogui.press('enter')

def get_last_chat_log(chat_region_pos):
    """채팅 내용을 긁어옵니다."""
    pyautogui.click(chat_region_pos)
    time.sleep(0.1)
    
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.1)
    
    return pyperclip.paste()

def parse_sell_result(text):
    """
    판매 결과에서 RARE 아이템 획득 여부 확인
    """
    if not text: return "NONE"
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines: return "NONE"
    
    user_name = MY_USER_NAME.strip()
    
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

                # RARE 아이템인지 확인 (목록에 있거나, 검/몽둥이가 아닌 경우)
                is_rare = any(rare_item in item_name for rare_item in RARE)
                is_weapon = "검" in item_name or "뭉둥이" in item_name or "몽둥이" in item_name

                if is_rare or not is_weapon:
                    print(f" >> [성공] RARE/특별 아이템 확보: {item_name}")
                    return "RARE_FOUND"
                else:
                    return "NORMAL_ITEM"
    return "NONE"

def parse_reinforce_result(text, last_level):
    """
    강화 결과 분석
    """
    if not text: return "NONE", last_level
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines: return "NONE", last_level
    
    user_name = MY_USER_NAME.strip()
    search_range = range(max(0, len(lines)-10), len(lines))

    for idx in reversed(list(search_range)):
        line = lines[idx]
        block_text = " ".join(lines[idx : idx + 3])

        if "부족" in block_text or "골드가 부족해" in block_text:
            return "GOLD_SHORTAGE", last_level
        
        if "성공" in block_text:
            match = re.search(r"→\s*\+(\d+)", block_text)
            if not match: match = re.search(r"\[\+(\d+)\]", block_text)
            if match: return "SUCCESS", int(match.group(1))

        if "유지" in block_text or "레벨이 유지" in block_text:
            return "MAINTAIN", last_level
        
        if "파괴" in block_text or "산산조각" in block_text:
            return "DESTROY", 0

    return "NONE", last_level

def main():
    print("=== 카카오톡 통합 강화 매크로 (Rare 획득 -> 목표 강화) ===")
    
    try:
        target_input = input(">> 목표 강화 수치를 입력하세요 (기본 15): ").strip()
        target_enforce = int(target_input) if target_input else TARGET_ENFORCE
    except ValueError:
        target_enforce = TARGET_ENFORCE

    print("\n[1단계] 마우스를 '채팅 입력창' 위에 올리세요.")
    input(">> 준비됐다면 Enter...")
    input_x, input_y = pyautogui.position()
    
    print("\n[2단계] 마우스를 '채팅 로그 영역' 위에 올리세요.")
    input(">> 준비됐다면 Enter...")
    chat_x, chat_y = pyautogui.position()
    
    print(f"\n[*] 설정 완료: RARE 아이템 탐색 -> +{target_enforce}강 목표")
    print("[*] 3초 뒤 시작합니다. (중단: ESC 꾹 누르기)")
    time.sleep(3)

    pos_input = (input_x, input_y)
    pos_chat = (chat_x, chat_y)
    
    state = "ACQUIRE" # ACQUIRE or ENFORCE
    count = 1
    current_level = 0

    send_mention_command(pos_input, "강화")

    while True:
        if state == "ACQUIRE":
            print(f"\n[{count}회차] '판매' 시도 (RARE 아이템 탐색 중...)")
            send_mention_command(pos_input, "판매")
            
            found = False
            for _ in range(12): # 응답 대기
                time.sleep(1)
                log_text = get_last_chat_log(pos_chat)
                res = parse_sell_result(log_text)
                
                if res == "RARE_FOUND":
                    print(" >> [전환] RARE 획득! 강화 단계로 이동합니다.")
                    state = "ENFORCE"
                    current_level = 0
                    found = True
                    break
                elif res == "NORMAL_ITEM":
                    print(" >> 일반 아이템입니다. 강화 후 다시 '판매'를 시도합니다.")
                    send_mention_command(pos_input, "강화")
                    time.sleep(WAIT_REPLY)
                    found = True
                    break
            if not found:
                print(" >> 응답 없음. 재시도합니다.")

        elif state == "ENFORCE":
            print(f"\n[{count}회차] '강화' 시도 (현재: +{current_level} / 목표: +{target_enforce})")
            send_mention_command(pos_input, "강화")
            
            found = False
            for _ in range(15): # 응답 대기
                time.sleep(1)
                log_text = get_last_chat_log(pos_chat)
                status, new_level = parse_reinforce_result(log_text, current_level)
                
                if status != "NONE":
                    print(f" >> 결과 확인: [{status}] 현재 수치: +{new_level}")
                    current_level = new_level
                    
                    if status == "DESTROY":
                        print(" >> [파괴] 아이템이 파괴되었습니다. 다시 탐색 단계로 돌아갑니다.")
                        state = "ACQUIRE"
                    elif status == "GOLD_SHORTAGE":
                        print(" >> [중단] 골드가 부족합니다.")
                        return
                    elif current_level >= target_enforce:
                        print(f" >> [완료] 목표 +{current_level}강 달성! 종료합니다.")
                        return
                    
                    found = True
                    break
            
            if not found:
                print(" >> 응답 없음. 재시도합니다.")

        count += 1
        time.sleep(1.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n사용자에 의해 종료되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
