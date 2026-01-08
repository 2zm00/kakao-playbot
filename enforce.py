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
    채팅 로그에서 @가 포함된 줄들을 먼저 추출한 뒤,
    내 이름(@MY_USER_NAME)이 언급된 가장 최근의 강화 결과를 분석합니다.
    """
    if not text:
        return "NONE", last_level

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    user_mention = f"@{MY_USER_NAME.strip()}"
    
    # 1. @가 포함된 줄들만 필터링 (사용자 제안 방식)
    # 하지만 결과 텍스트가 여러 줄에 걸쳐 있을 수 있으므로, 
    # 원본 줄 번호를 유지하며 @이 포함된 줄의 인덱스를 찾습니다.
    mention_indices = [i for i, line in enumerate(lines) if "@" in line]
    
    # 2. 뒤에서부터 확인하여 내 이름이 포함된 가장 최근의 멘션 줄을 찾음
    for idx in reversed(mention_indices):
        line = lines[idx]
        
        # 내 이름 멘션 확인
        if user_mention in line:
            # 3. 해당 줄부터 아래로 몇 줄(메시지 블록)을 묶어서 분석
            search_block = lines[idx : idx + 6]
            block_text = " ".join(search_block)
            
            # 골드 부족 확인
            if "부족" in block_text or "골드가 부족해" in block_text:
                return "GOLD_SHORTAGE", last_level
            
            # 결과 키워드 및 수치 파싱
            if "강화 성공" in block_text:
                match = re.search(r"→\s*\+(\d+)", block_text)
                if match:
                    return "SUCCESS", int(match.group(1))
                # ⚔️획득 검 패턴 재확인
                match = re.search(r"\[\+(\d+)\]", block_text)
                if match:
                    return "SUCCESS", int(match.group(1))

            elif "강화 유지" in block_text or "레벨이 유지되었습니다" in block_text:
                return "MAINTAIN", last_level
            
            elif "강화 파괴" in block_text or "산산조각" in block_text:
                return "DESTROY", 0
                
            # 만약 내 멘션은 찾았는데 위 결과들이 하나도 없다면, 
            # 아직 봇 응답이 덜 온 것일 수 있으므로 계속 기다려야 함 (NONE 반환)
            break 
            
    return "NONE", last_level

def main():
    print(f"=== 카카오톡 강화 봇 V4 (사용자: {MY_USER_NAME}, 목표: +{TARGET_ENFORCE}강) ===")
    print("설정을 위해 두 번의 좌표 입력이 필요합니다.")
    print("\n[1단계] 마우스를 '채팅 입력창' 위에 올리세요.")
    input(">> 준비됐다면 Enter...")
    input_x, input_y = pyautogui.position()
    
    print("\n[2단계] 마우스를 '채팅 로그 영역' 위에 올리세요.")
    input(">> 준비됐다면 Enter...")
    chat_x, chat_y = pyautogui.position()
    
    print(f"\n[*] 목표 수치: +{TARGET_ENFORCE}강 도달 시 중단합니다.")
    print("[*] 3초 뒤 시작됩니다. 중단하려면 ESC를 꾹 누르세요.")
    time.sleep(3)

    count = 1
    current_level = 0
    pos_input = (input_x, input_y)
    pos_chat = (chat_x, chat_y)

    while True:
        print(f"\n[{count}회차] 강화 명령 전송 중... (현재: +{current_level}강)")
        
        # 1. 강화 시도
        send_mention_command(pos_input, "강화")
        
        # 2. 결과가 나올 때까지 대기 (명령어 중복 방지)
        print(" >> 응답 대기 중", end="", flush=True)
        status = "NONE"
        new_level = current_level
        
        # 최대 15초 동안 1초 간격으로 확인
        for _ in range(15):
            time.sleep(1.0)
            print(".", end="", flush=True)
            
            log_text = get_last_chat_log(pos_chat)
            status, new_level = parse_reinforce_result(log_text, current_level)
            
            if status != "NONE":
                print(f" 확인됨! [{status}]")
                break
        
        # 3. 결과에 따른 처리
        if status == "GOLD_SHORTAGE":
            print("!!! 골드가 부족하여 봇을 중단합니다 !!!")
            break
            
        if status == "NONE":
            print("\n >> [경고] 15초 동안 결과를 찾지 못했습니다. 다시 명령을 보냅니다.")
            continue # count 증가 없이 루프 처음으로 (재시도)

        # 수치 업데이트 및 종료 조건 확인
        current_level = new_level
        if current_level >= TARGET_ENFORCE:
            print(f"✨ 목표 수치 +{current_level}강 도달! 강화봇을 종료합니다. ✨")
            break
            
        count += 1
        time.sleep(1.5) # 다음 시도 전 매너 휴식

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n사용자에 의해 종료되었습니다.")
    except SystemExit:
        pass
