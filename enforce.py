import pyautogui
import pyperclip
import time
import sys
import re
import config

# === 설정 (CONFIG) ===
BOT_NAME = config.BOT_NAME
MY_USER_NAME = config.MY_USER_NAME  
DELAY = 0.5
WAIT_REPLY = float(config.WAIT_REPLY)
TARGET_ENFORCE = int(config.TARGET_ENFORCE)

def clipboard_input(text):
    """클립보드를 이용한 한글 입력"""
    pyperclip.copy(text)
    time.sleep(0.1) 
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.1)

def send_mention_command(input_pos, command):
    """@플 -> 탭 -> 명령어 -> 엔터"""
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

def parse_reinforce_result(text, last_level):
    """
    채팅 로그에서 강화 결과 분석
    반환값: (상태, 새로운 수치)
    """
    if not text:
        return "NONE", last_level

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines:
        return "NONE", last_level
        
    user_name = MY_USER_NAME.strip()
    
    # 1. 내 이름이 포함된 줄 찾기
    mention_indices = [i for i, line in enumerate(lines) if user_name in line]
    
    if not mention_indices:
        # 멘션이 없더라도 마지막 10줄에서 키워드 검색
        search_range = range(max(0, len(lines)-10), len(lines))
    else:
        # 마지막 멘션부터 아래로 10줄 검색
        last_idx = mention_indices[-1]
        search_range = range(last_idx, min(len(lines), last_idx + 10))

    for idx in reversed(list(search_range)):
        line = lines[idx]
        block_text = " ".join(lines[idx : idx + 3]) # 주변 줄까지 살짝 묶어서 확인

        # [1] 골드 부족
        if "부족" in block_text or "골드가 부족해" in block_text:
            return "GOLD_SHORTAGE", last_level
        
        # [2] 강화 성공
        if "성공" in block_text and "→" in block_text:
            match = re.search(r"→\s*\+(\d+)", block_text)
            if match:
                return "SUCCESS", int(match.group(1))
            
        # [3] 강화 성공 (다른 패턴: [+17])
        if "성공" in block_text and "[+" in block_text:
            match = re.search(r"\[\+(\d+)\]", block_text)
            if match:
                return "SUCCESS", int(match.group(1))

        # [4] 강화 유지
        if "유지" in block_text or "레벨이 유지" in block_text:
            return "MAINTAIN", last_level
        
        # [5] 강화 파괴
        if "파괴" in block_text or "산산조각" in block_text:
            return "DESTROY", 0

    return "NONE", last_level

def main():
    print(f"=== 카카오톡 강화 봇 (사용자: {MY_USER_NAME}) ===")
    
    # 목표 수치 입력 받기
    try:
        target_input = input(">> 목표 강화 수치를 입력하세요 (예: 15): ").strip()
        target_enforce = int(target_input) if target_input else TARGET_ENFORCE
    except ValueError:
        target_enforce = TARGET_ENFORCE

    print("\n[1단계] 마우스를 '채팅 입력창' 위에 올리세요.")
    input(">> 준비됐다면 Enter...")
    input_x, input_y = pyautogui.position()
    
    print("\n[2단계] 마우스를 '채팅 로그 영역' 위에 올리세요.")
    input(">> 준비됐다면 Enter...")
    chat_x, chat_y = pyautogui.position()
    
    print(f"\n[*] 목표 수치: +{target_enforce}강 도달 시 중단합니다.")
    print("[*] 3초 뒤 시작됩니다. 중단하려면 ESC를 꾹 누르세요.")
    time.sleep(3)

    count = 1
    current_level = 0
    pos_input = (input_x, input_y)
    pos_chat = (chat_x, chat_y)

    while True:
        print(f"\n[{count}회차] 강화 시도 (현재: +{current_level}강 / 목표: +{target_enforce}강)")
        
        # 1. 강화 명령 전송
        send_mention_command(pos_input, "강화")
        
        # 2. 결과가 나올 때까지 대기
        status = "NONE"
        new_level = current_level
        print(" >> 응답 대기 중", end="", flush=True)
        
        for _ in range(15): # 최대 15초 대기
            time.sleep(1.0)
            print(".", end="", flush=True)
            
            log_text = get_last_chat_log(pos_chat)
            status, new_level = parse_reinforce_result(log_text, current_level)
            
            if status != "NONE":
                print(f" 확인됨! [{status}] 수치: +{new_level}")
                break
        
        # 3. 결과에 따른 처리
        if status == "GOLD_SHORTAGE":
            print("\n!!! 골드가 부족하여 봇을 중단합니다 !!!")
            break
            
        if status == "NONE":
            print("\n >> [경고] 결과를 찾지 못했습니다. 다시 시도합니다.")
            continue # count 증가 없이 재시도

        # 수치 업데이트 및 종료 조건 확인
        current_level = new_level
        if current_level >= target_enforce:
            print(f"\n✨ 목표 수치 +{current_level}강 도달! 강화봇을 종료합니다. ✨")
            break
            
        count += 1
        time.sleep(1.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n사용자에 의해 종료되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
