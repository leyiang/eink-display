import pyautogui

def getCursorInfo():
    try:
        cursor = pyautogui.position()
        return [ cursor.x, cursor.y ]
    except:
        print("oh noo...")
        pass