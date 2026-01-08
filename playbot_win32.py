import time
import win32gui
import win32con
import win32api
import pyperclip

# === 설정 ===
CHAT_ROOM_NAME = "플레이봇"  # 카카오톡 채팅방 제목(창 이름)

def kakao_send_text(hwnd, text):
    """
    핸들(hwnd)을 가진 창에 텍스트를 붙여넣고 엔터를 치는 비활성 입력 시도
    """
    # 1. 텍스트를 클립보드에 복사
    pyperclip.copy(text)
    
    # 2. 해당 윈도우에 '붙여넣기(Ctrl+V)' 메세지 전송
    # WM_KEYDOWN 등의 키보드 메시지를 직접 보내는 방식
    
    # Ctrl 키 누름
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_CONTROL, 0)
    time.sleep(0.01)
    # V 키 누름
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, ord('V'), 0)
    time.sleep(0.01)
    # V 키 뗌
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, ord('V'), 0)
    time.sleep(0.01)
    # Ctrl 키 뗌
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_CONTROL, 0)
    
    time.sleep(0.1)
    
    # 3. 엔터 키 전송
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
    time.sleep(0.01)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)

def find_kakao_window(room_name):
    """제목이 room_name인 카카오톡 채팅방 핸들을 찾음"""
    hwnd = win32gui.FindWindow(None, room_name)
    if hwnd == 0:
        print(f"[!] '{room_name}' 채팅방을 찾을 수 없습니다.")
        return None
    
    # 카카오톡 채팅방 내부의 'RichEdit' 컨트롤(입력창)을 찾아야 함
    # 구조: ChatRoom -> EVA_Window -> Edit
    # 하지만 카톡 업데이트마다 클래스명이 바뀌어 찾기가 매우 까다로움.
    # 일단 채팅방 메인 핸들(hwnd)에 키 입력을 보내보는 방식으로 시도.
    return hwnd

def main():
    print("=== 비활성 입력 테스트 ===")
    hwnd = find_kakao_window(CHAT_ROOM_NAME)
    
    if hwnd:
        print(f"[*] 채팅방 핸들 발견: {hwnd}")
        print("[*] 3초 뒤 테스트 메시지를 보냅니다. 마우스를 딴데 두고 보세요.")
        time.sleep(3)
        
        kakao_send_text(hwnd, "테스트 메시지입니다")
        print("[*] 전송 신호 보냄 완료")
    else:
        print("카카오톡 채팅방을 띄워주세요.")

if __name__ == "__main__":
    main()
