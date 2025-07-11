#!/usr/bin/env python3
"""
鼠标磁铁效果模块
当鼠标靠近指定X轴位置时，会有磁力将鼠标吸引到该位置
"""

import time
import math
import threading
from pynput import mouse
import tkinter as tk


class MouseMagnet:
    def __init__(self, magnet_positions=None, magnet_radius=200, force_strength=0.3, update_interval=0.01):
        """
        初始化鼠标磁铁
        
        Args:
            magnet_positions: 磁铁X轴位置列表，如果为None则使用屏幕中心
            magnet_radius: 磁力作用半径（像素）
            force_strength: 磁力强度（0-1之间）
            update_interval: 更新间隔（秒）
        """
        self.magnet_radius = magnet_radius
        self.force_strength = force_strength
        self.update_interval = update_interval
        self.running = False
        self.mouse_controller = mouse.Controller()
        
        # 获取单个显示器尺寸
        self.screen_width = self._get_screen_width()
        
        # 设置磁铁X轴位置列表
        if magnet_positions is None:
            self.magnet_positions = [self.screen_width // 2]
        else:
            self.magnet_positions = magnet_positions.copy()
        
        print(f"磁铁X轴位置: {self.magnet_positions}")
        print(f"磁力半径: {self.magnet_radius}px")
        print(f"磁力强度: {self.force_strength}")
    
    def _get_screen_width(self):
        """获取单个显示器宽度"""
        root = tk.Tk()
        root.withdraw()
        
        try:
            import subprocess
            result = subprocess.run(['xrandr'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for line in lines:
                if ' connected primary' in line or (' connected' in line and 'primary' not in result.stdout):
                    parts = line.split()
                    for part in parts:
                        if 'x' in part and part.replace('x', '').replace('+', '').replace('-', '').isdigit():
                            width = int(part.split('x')[0])
                            if 800 <= width <= 4000:
                                root.destroy()
                                return width
                    break
            else:
                raise Exception("无法从xrandr获取分辨率")
        except:
            total_width = root.winfo_screenwidth()
            if total_width > 3000:
                width = 1920
            else:
                width = total_width
            root.destroy()
            return width
    
    def add_magnet_position(self, x):
        """添加磁铁X轴位置"""
        if x not in self.magnet_positions:
            self.magnet_positions.append(x)
            print(f"添加磁铁位置: {x}, 当前所有位置: {self.magnet_positions}")
        else:
            print(f"磁铁位置 {x} 已存在")
    
    def clear_magnet_positions(self):
        """清除所有磁铁位置"""
        self.magnet_positions.clear()
        print("已清除所有磁铁位置")
    
    def get_current_mouse_x(self):
        """获取当前鼠标X轴位置"""
        return self.mouse_controller.position[0]
    
    def calculate_distance(self, x1, y1, x2, y2):
        """计算两点间距离"""
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    
    def apply_magnet_force(self):
        """应用磁铁效果（仅X轴，支持多个磁铁位置）"""
        if not self.magnet_positions:
            return
        
        current_pos = self.mouse_controller.position
        current_x, current_y = current_pos
        
        # 找到最近的磁铁位置
        closest_magnet = None
        min_distance = float('inf')
        
        for magnet_x in self.magnet_positions:
            distance = abs(current_x - magnet_x)
            if distance < min_distance and distance < self.magnet_radius:
                min_distance = distance
                closest_magnet = magnet_x
        
        # 如果找到了在有效范围内的磁铁，应用磁力
        if closest_magnet is not None and min_distance > 5:  # 避免在磁铁点抖动
            # 计算磁力强度（距离越近，磁力越强）
            force_factor = (self.magnet_radius - min_distance) / self.magnet_radius
            # 增强拖拽力度
            actual_force = self.force_strength * force_factor * 2.0
            
            # 计算X轴移动向量
            dx = closest_magnet - current_x
            
            # 应用磁力（仅X轴）
            new_x = current_x + dx * actual_force
            new_y = current_y  # Y轴保持不变
            
            # 移动鼠标
            self.mouse_controller.position = (new_x, new_y)
    
    def magnet_loop(self):
        """磁铁效果主循环"""
        while self.running:
            try:
                self.apply_magnet_force()
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"磁铁效果错误: {e}")
                break
    
    def start(self):
        """启动磁铁效果"""
        if not self.running:
            self.running = True
            self.magnet_thread = threading.Thread(target=self.magnet_loop, daemon=True)
            self.magnet_thread.start()
            print("鼠标磁铁效果已启动")
            print("按 Ctrl+C 退出")
    
    def stop(self):
        """停止磁铁效果"""
        self.running = False
        print("鼠标磁铁效果已停止")


def main():
    # 创建磁铁实例
    magnet = MouseMagnet(
        magnet_radius=200,    # 磁力半径200像素
        force_strength=0.3,   # 磁力强度30%
        update_interval=0.008 # 8ms更新一次，保证流畅
    )
    
    try:
        # 启动磁铁效果
        magnet.start()
        
        # 保持程序运行
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n正在退出...")
        magnet.stop()
        print("程序已退出")


if __name__ == "__main__":
    main()