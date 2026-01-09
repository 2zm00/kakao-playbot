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
RARE = ["광선검", "핫도그", "칫솔", "주전자", "채찍", "꽃다발"]

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
    채팅 로그에서 '판매' 결과로 나온 아이템 확인
    안내: "⚔️새로운 검 획득: [+0] (무기종류)"
    반환값: 
      - "STOP": 레어템이거나, 검/몽둥이가 아님
      - "ENFORCE": 일반 검/몽둥이 획득 (강화 진행)
      - "NONE": 내 멘션이나 결과를 찾지 못함
    """
    if not text:
        return "NONE"

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines:
        return "NONE"
        
    user_name = MY_USER_NAME.strip()
    user_mention = f"@{user_name}"
    
    # 디버깅: 마지막 5줄 출력 (주석 해제 시 활성화 가능)
    # print(f"\n[DEBUG] 최근 로그: {lines[-5:]}")
    
    # 1. 내 멘션이 포함된 줄 찾기
    mention_indices = [i for i, line in enumerate(lines) if user_name in line]
    
    if not mention_indices:
        # 혹시 멘션 없이 결과만 나올 경우를 대비해 마지막 10줄에서 검색
        search_range = range(max(0, len(lines)-10), len(lines))
    else:
        # 마지막 멘션부터 아래로 10줄 검색
        last_idx = mention_indices[-1]
        search_range = range(last_idx, min(len(lines), last_idx + 10))

    for idx in reversed(list(search_range)):
        line = lines[idx]
        
        # "획득:" 패턴 매칭
        # 예: ⚔️새로운 검 획득: [+0] 낡은 검
        # 또는: @사용자님 ⚔️새로운 검 획득: [+0] 낡은 검
        if "획득:" in line and "[+0]" in line:
            # 정규표현식으로 아이템 이름 추출
            # [+0] 이후의 첫 단어 또는 끝까지의 문자열을 가져옴
            match = re.search(r"\[\+0\]\s*([^\s(].*)", line)
            if not match:
                # 줄 바꿈으로 인해 다음 줄에 있을 수도 있음
                if idx + 1 < len(lines):
                    next_line = lines[idx + 1]
                    match = re.search(r"^([^\s(].*)", next_line)
            
            if match:
                item_name = match.group(1).strip()
                # 괄호 등이 포함된 경우 제거 (예: "낡은 검 (추가내용)")
                item_name = re.split(r"[\(\[]", item_name)[0].strip()
                
                print(f"\n >> [감지] 획득 아이템: {item_name}")

                # 1. RARE 목록에 있는지 확인
                if any(rare_item in item_name for rare_item in RARE):
                    print(f" >> [중단] RARE 아이템 발견: {item_name}")
                    return "STOP"

                # 2. 검 또는 몽둥이(뭉둥이)인지 확인
                if "검" in item_name or "뭉둥이" in item_name or "몽둥이" in item_name:
                    return "ENFORCE"
                else:
                    print(f" >> [중단] 대상 외 아이템: {item_name}")
                    return "STOP"

    return "NONE"

def main():
    print("=== 카카오톡 자동화 봇 (판매 -> 강화 루틴) ===")
    
    print("\n[1단계] 마우스를 '채팅 입력창' 위에 올리세요.")
    input(">> 준비됐다면 Enter...")
    input_x, input_y = pyautogui.position()
    
    print("\n[2단계] 마우스를 '채팅 로그 영역' 위에 올리세요.")
    input(">> 준비됐다면 Enter...")
    chat_x, chat_y = pyautogui.position()
    
    print("\n[*] 3초 뒤 시작됩니다. 중단하려면 ESC를 꾹 누르세요.")
    time.sleep(3)

    count = 1
    pos_input = (input_x, input_y)
    pos_chat = (chat_x, chat_y)

    while True:
        print(f"\n[{count}회차] '판매' 명령 전송")
        send_mention_command(pos_input, "판매")
        
        # 응답 대기 및 분석
        found_result = False
        print(" >> 결과 대기 중", end="", flush=True)
        
        for _ in range(12): # 최대 12초 대기
            time.sleep(1.0)
            print(".", end="", flush=True)
            
            log_text = get_last_chat_log(pos_chat)
            result = parse_sell_result(log_text)
            
            if result == "STOP":
                print("\n[*] 조건을 만족하지 않거나 레어템 획득. 종료합니다.")
                return
            
            if result == "ENFORCE":
                print("\n >> [판단] 일반 무기 획득! '강화' 전송")
                send_mention_command(pos_input, "강화")
                found_result = True
                break
                
        if not found_result:
            print("\n >> [경고] 결과를 찾지 못했습니다. 로그를 다시 확인하거나 좌표를 체크해보세요.")
        
        count += 1
        time.sleep(1.5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n중단되었습니다.")
    except Exception as e:  
        print(f"\n오류 발생: {e}")
