import pyautogui
import pyperclip
import time
import sys
import config

# === 설정 (CONFIG) ===
# config.py에서 값을 불러오되, 안전을 위해 기본 딜레이를 넉넉히 잡습니다.
# 입력이 자꾸 씹히면 이 값들을 0.1~0.2씩 늘려주세요.
BOT_NAME = config.BOT_NAME  # "@플"
DELAY = 0.5                 # 기본 입력 간격 (안정성을 위해 0.5초 권장)
WAIT_REPLY = float(config.WAIT_REPLY) # 봇 응답 대기 시간

def clipboard_input(text):
    """클립보드를 이용한 한글 입력 (딜레이 보정)"""
    pyperclip.copy(text)
    # 복사 후 클립보드 반영 대기
    time.sleep(0.1) 
    pyautogui.hotkey('ctrl', 'v')
    # 붙여넣기 후 입력창 반영 대기 (중요)
    time.sleep(0.1)

def send_mention_command(input_pos, command):
    """
    @플 -> 탭 -> (대기) -> 명령어 -> 엔터
    """
    # 0. 입력창 클릭 (커서 활성화)
    pyautogui.click(input_pos)
    time.sleep(0.1)
    
    # 1. 봇 호출 (@플)
    clipboard_input(BOT_NAME) 
    time.sleep(DELAY)
    
    # 2. 탭으로 멘션 확정
    pyautogui.press('tab')
    
    # [핵심 수정] 탭 직후 커서가 깜빡이며 준비될 때까지 충분히 대기
    # 컴퓨터 성능에 따라 이 시간이 짧으면 명령어가 씹힙니다.
    time.sleep(DELAY + 0.2) 
    
    # 3. 명령어 입력 (강화/판매)
    clipboard_input(command)
    time.sleep(DELAY)
    
    # 4. 전송
    pyautogui.press('enter')

def check_esc_pressed():
    """ESC 키 감지 시 종료"""

    print("\n[!] ESC 키가 감지되었습니다. 안전하게 종료합니다.")


def parse_last_result(text):
    """
    채팅 로그에서 최근 메시지를 분석하여 '검' 또는 '몽둥이' 획득 여부를 판단
    """
    if not text:
        return False

    lines = text.strip().split('\n')
    
    # 최근 20줄만 역순으로 검사 (너무 옛날 로그는 무시)
    scan_range = min(len(lines), 20)
    target_lines = lines[-scan_range:]
    
    found_item = False
    
    for line in reversed(target_lines):
        line = line.strip()
        
        # 1. '몽둥이'는 발견 즉시 성공으로 간주 (라벨과 겹칠 일 없음)
        if "몽둥이" in line:
            print(f" >> 아이템 발견(몽둥이): {line}")
            found_item = True
            break
            
        # 2. '검'은 '획득 검:' 라벨과 구분 필요
        if "검" in line:
            # "⚔️획득 검:" 같은 라벨이 포함된 줄이라면, 라벨을 제외한 뒷부분만 검사
            if "획득 검:" in line:
                # "⚔️획득 검: [+1] 나무 검" -> split 결과: ["⚔️", " [+1] 나무 검"]
                parts = line.split("획득 검:")
                if len(parts) > 1:
                    item_name = parts[1]
                    if "검" in item_name:
                        print(f" >> 아이템 발견(검): {line}")
                        found_item = True
                        break
            # 라벨이 없는 줄(예: "[+1] 나무 검")에서 발견된 경우
            elif "획득" not in line: 
                 # 단순히 설명에 '검'이 들어가는 경우를 배제하려면 정교한 조건 필요하지만,
                 # 게임 특성상 아이템 이름 줄일 확률이 높으므로 일단 인정
                 print(f" >> 아이템 발견(검 추정): {line}")
                 found_item = True
                 break

    return found_item

def get_last_chat_log(chat_region_pos):
    """채팅 내용을 긁어옵니다."""
    # 채팅창 클릭
    pyautogui.click(chat_region_pos)
    time.sleep(0.1)
    
    # 전체 선택 -> 복사
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.1)
    
    
    return pyperclip.paste()

def main():
    print("=== 카카오톡 자동화 봇 V3 (좌표 기반 포커스 전환) ===")
    print("설정을 위해 두 번의 좌표 입력이 필요합니다.")
    print("\n[1단계] 마우스를 '채팅 입력창(글자 쓰는 곳)' 위에 올리세요.")
    input(">> 준비됐다면 Enter...")
    input_x, input_y = pyautogui.position()
    print(f"[*] 입력창 좌표 저장: ({input_x}, {input_y})")
    
    print("\n[2단계] 마우스를 '채팅 로그 영역(노란/하늘색 빈 공간)' 위에 올리세요.")
    input(">> 준비됐다면 Enter...")
    chat_x, chat_y = pyautogui.position()
    print(f"[*] 채팅창 좌표 저장: ({chat_x}, {chat_y})")
    
    print("\n[*] 3초 뒤 시작됩니다. 중단하려면 ESC를 꾹 누르세요.")
    time.sleep(3)

    count = 1
    # 입력창/채팅창 좌표를 튜플로 묶어서 사용
    pos_input = (input_x, input_y)
    pos_chat = (chat_x, chat_y)

    while True:
        print(f"\n[{count}회차] 루프 시작")
        
        # [1] 초기 강화 (항상 입력창 클릭부터 시작함)
        send_mention_command(pos_input, "강화")
        
        # 응답 대기
        start_t = time.time()
        while time.time() - start_t < WAIT_REPLY:

            time.sleep(0.1)
            
        # [2] 판독 (채팅창 클릭 -> 복사)
        log_text = get_last_chat_log(pos_chat)
        is_good_item = parse_last_result(log_text)
        
        if is_good_item:
            print(" >> [판단] 검/몽둥이 획득! (강화 -> 판매)")
            

            send_mention_command(pos_input, "강화")
            time.sleep(WAIT_REPLY)
            

            send_mention_command(pos_input, "판매")
            print(" >> 판매 완료")
        else:
            print(" >> [판단] 꽝 (강화 -> 다음 턴)")
            

            send_mention_command(pos_input, "강화")
            print(" >> 강화 후 턴 종료")
            
        count += 1
        time.sleep(1.0) # 사이클 간 휴식

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except SystemExit:
        pass
