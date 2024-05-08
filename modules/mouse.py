import pyautogui

def getCursorInfo():
    cursor = pyautogui.position()
    return [ cursor.x, cursor.y ]