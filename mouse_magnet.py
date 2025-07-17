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
    # 预设环境配置 - 格式: {"env_name": {"positions": [x1, x2, ...], "frame_size": [width, height]}}
    PRESET_ENVIRONMENTS = {
        "nndesign": {"positions": [2021], "frame_size": [788, 492]},
        "thomas": {"positions": [2106, 2204], "frame_size": [808, 505]},
        "advanced-engineer-math": {"positions": [1790, 1743], "frame_size": [828, 523]}, 
    }

    def __init__(self, magnet_positions=None, magnet_radius=200, force_strength=0.3, update_interval=0.01, capture_mode_check=None, dead_zone=30):
        """
        初始化鼠标磁铁
        
        Args:
            magnet_positions: 磁铁X轴位置列表，如果为None则使用屏幕中心
            magnet_radius: 磁力作用半径（像素）
            force_strength: 磁力强度（0-1之间）
            update_interval: 更新间隔（秒）
            capture_mode_check: 检查是否为捕获模式的回调函数
            dead_zone: 死区范围（像素），在此范围内鼠标X轴完全锁定
        """
        self.magnet_radius = magnet_radius
        self.force_strength = force_strength
        self.update_interval = update_interval
        self.running = False
        self.paused = False  # 新增暂停状态
        self.mouse_controller = mouse.Controller()
        self.capture_mode_check = capture_mode_check
        self.dead_zone = dead_zone
        self.scroll_pause_time = 0
        self.scroll_pause_duration = 0.5  # 滚轮操作后暂停磁力0.5秒
        self.mouse_listener = None
        
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
        print(f"死区范围: {self.dead_zone}px")
    
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
    
    def rotate_magnet_positions(self):
        """旋转磁铁位置列表：[a, b, c] => [b, c, a]"""
        if len(self.magnet_positions) > 1:
            first = self.magnet_positions.pop(0)
            self.magnet_positions.append(first)
            print(f"磁铁位置已旋转，当前激活位置: {self.magnet_positions[0]}, 所有位置: {self.magnet_positions}")
        else:
            print("磁铁位置少于2个，无需旋转")
    
    def clear_magnet_positions(self):
        """清除所有磁铁位置"""
        self.magnet_positions.clear()
        print("已清除所有磁铁位置")

    def load_preset_environment(self, env_name):
        """加载预设环境配置"""
        if env_name in self.PRESET_ENVIRONMENTS:
            env_config = self.PRESET_ENVIRONMENTS[env_name]
            self.magnet_positions = env_config["positions"].copy()
            print(f"已加载预设环境 '{env_name}': 磁铁位置 {self.magnet_positions}, 帧尺寸 {env_config['frame_size']}")
            return env_config
        else:
            print(f"预设环境 '{env_name}' 不存在")
            print(f"可用环境: {list(self.PRESET_ENVIRONMENTS.keys())}")
            return None

    def get_available_environments(self):
        """获取可用的预设环境列表"""
        return list(self.PRESET_ENVIRONMENTS.keys())
    
    def get_current_mouse_x(self):
        """获取当前鼠标X轴位置"""
        return self.mouse_controller.position[0]
    
    def calculate_distance(self, x1, y1, x2, y2):
        """计算两点间距离"""
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    
    def on_scroll(self, x, y, dx, dy):
        """滚轮事件处理，暂停磁力效果"""
        self.scroll_pause_time = time.time()
    
    def apply_magnet_force(self):
        """应用磁铁效果（仅X轴，仅使用第一个磁铁位置）"""
        if not self.magnet_positions:
            return
        
        # 检查是否暂停
        if self.paused:
            return
        
        # 检查是否为捕获模式，如果不是则不应用磁力
        if self.capture_mode_check and not self.capture_mode_check():
            return
        
        # 检查是否在滚轮暂停期间
        if time.time() - self.scroll_pause_time < self.scroll_pause_duration:
            return
        
        current_pos = self.mouse_controller.position
        current_x, current_y = current_pos
        
        # 仅使用第一个磁铁位置
        active_magnet = self.magnet_positions[0]
        distance = abs(current_x - active_magnet)
        
        # 检查是否在磁力作用范围内
        if distance < self.magnet_radius:
            # 死区机制：在死区范围内完全锁定X轴位置
            if distance <= self.dead_zone:
                # 完全锁定在磁铁位置
                self.mouse_controller.position = (active_magnet, current_y)
            else:
                # 在死区外应用磁力
                # 计算磁力强度（距离越近，磁力越强）
                force_factor = (self.magnet_radius - distance) / self.magnet_radius
                # 增强拖拽力度
                actual_force = self.force_strength * force_factor * 2.0
                
                # 计算X轴移动向量
                dx = active_magnet - current_x
                
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
            # 不再启动独立的鼠标监听器，由主程序处理滚动事件
            self.magnet_thread = threading.Thread(target=self.magnet_loop, daemon=True)
            self.magnet_thread.start()
            print("鼠标磁铁效果已启动")
            print("按 Ctrl+C 退出")
    
    def pause(self):
        """暂停磁铁效果"""
        self.paused = True
        print("鼠标磁铁效果已暂停")
    
    def resume(self):
        """恢复磁铁效果"""
        self.paused = False
        print("鼠标磁铁效果已恢复")
    
    def toggle_pause(self):
        """切换暂停/恢复状态"""
        if self.paused:
            self.resume()
        else:
            self.pause()
        return not self.paused  # 返回当前是否为激活状态
    
    def is_paused(self):
        """检查是否暂停"""
        return self.paused
    
    def stop(self):
        """停止磁铁效果"""
        self.running = False
        print("鼠标磁铁效果已停止")


def main():
    # 创建磁铁实例
    magnet = MouseMagnet(
        magnet_radius=200,    # 磁力半径200像素
        force_strength=0.3,   # 磁力强度30%
        update_interval=0.008, # 8ms更新一次，保证流畅
        dead_zone=30          # 死区范围30像素
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
