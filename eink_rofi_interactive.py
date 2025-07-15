#!/usr/bin/env python

"""
E-ink Display Interactive Settings Menu (Python版本)
这个脚本创建一个交互式rofi菜单用于连续数值调整
"""

import os
import sys
import time
import subprocess
from typing import Optional

# 添加modules目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from RofiHelper import RofiHelper


class EinkRofiMenu:
    """E-ink设备的Rofi交互菜单"""

    def __init__(self, pipe_path: str = "/tmp/eink_control"):
        self.pipe_path = pipe_path
        self.rofi = RofiHelper()

    def check_app_running(self) -> bool:
        """检查e-ink应用是否正在运行"""
        return os.path.exists(self.pipe_path)

    def send_command(self, command: str) -> None:
        """发送命令到e-ink应用"""
        try:
            with open(self.pipe_path, 'w') as pipe:
                pipe.write(command)
                pipe.flush()
        except Exception as e:
            print(f"Error sending command '{command}': {e}")


    def adjust_threshold(self) -> None:
        """交互式阈值调整"""
        last_selected = 1  # 默认选中增加

        while True:
            options = [
                "🔧 Threshold Settings",
                "➕ Increase (+10)",
                "➖ Decrease (-10)",
                "🔄 Toggle (120/180)",
                "↩️ Back to Main Menu"
            ]

            choice = self.rofi.show_interactive_menu(
                options=options,
                selected_row=last_selected,
                prompt="Threshold Adjustment"
            )

            if not choice or choice in ["↩️ Back to Main Menu", ""]:
                break
            elif choice == "➕ Increase (+10)":
                self.send_command("thresh_up")
                last_selected = 1
            elif choice == "➖ Decrease (-10)":
                self.send_command("thresh_down")
                last_selected = 2
            elif choice == "🔄 Toggle (120/180)":
                self.send_command("thresh_toggle")
                last_selected = 3

    def adjust_size(self) -> None:
        """交互式大小调整"""
        last_selected = 1

        while True:
            options = [
                "📏 Size Settings",
                "➕ Increase Size",
                "➖ Decrease Size",
                "↩️ Back to Main Menu"
            ]

            choice = self.rofi.show_interactive_menu(
                options=options,
                selected_row=last_selected,
                prompt="Size Adjustment"
            )

            if not choice or choice in ["↩️ Back to Main Menu", ""]:
                break
            elif choice == "➕ Increase Size":
                self.send_command("size_up")
                last_selected = 1
            elif choice == "➖ Decrease Size":
                self.send_command("size_down")
                last_selected = 2

    def adjust_ratio(self) -> None:
        """交互式比例调整"""
        last_selected = 1

        while True:
            options = [
                "📐 Ratio Settings",
                "➕ Increase Ratio",
                "➖ Decrease Ratio",
                "↩️ Back to Main Menu"
            ]

            choice = self.rofi.show_interactive_menu(
                options=options,
                selected_row=last_selected,
                prompt="Ratio Adjustment"
            )

            if not choice or choice in ["↩️ Back to Main Menu", ""]:
                break
            elif choice == "➕ Increase Ratio":
                self.send_command("ratio_up")
                last_selected = 1
            elif choice == "➖ Decrease Ratio":
                self.send_command("ratio_down")
                last_selected = 2

    def adjust_magnet_environment(self) -> bool:
        """交互式磁铁环境选择"""
        last_selected = 1

        while True:
            options = [
                "🧲 Magnet Environment Settings",
                "🔧 nndesign ([2021], 788x492)",
                "🔧 thomas ([2106, 2204], 808x505)",
                "↩️ Back to Main Menu"
            ]

            choice = self.rofi.show_interactive_menu(
                options=options,
                selected_row=last_selected,
                prompt="Magnet Environment Selection"
            )

            if not choice or choice in ["↩️ Back to Main Menu", ""]:
                return False  # 返回False表示没有选择环境
            elif choice == "🔧 nndesign ([2021], 788x492)":
                self.send_command("magnet_nndesign")
                return True  # 返回True表示选择了环境
            elif choice == "🔧 thomas ([2106, 2204], 808x505)":
                self.send_command("magnet_thomas")
                return True  # 返回True表示选择了环境

    def run_main_menu(self) -> None:
        """运行主菜单"""
        while True:
            options = [
                "🔧 Adjust Threshold (Interactive)",
                "🧲 Start Magnet",
                "🚫 Stop Magnet",
                "⚡ Magnet Environments",
                "📏 Adjust Size (Interactive)",
                "📐 Adjust Ratio (Interactive)",
                "🎯 Toggle Capture Mode",
                "⏸️ Toggle Stop/Start",
                "🔄 Refresh Display",
                "🖱️ Select Area (slop)",
                "❌ Exit"
            ]

            choice = self.rofi.show_main_menu(
                options=options,
                prompt="E-ink Settings"
            )

            if not choice or choice in ["❌ Exit", ""]:
                break
            elif choice == "🧲 Start Magnet":
                self.send_command("start_magnet")
                break  # 退出菜单
            elif choice == "🚫 Stop Magnet":
                self.send_command("stop_magnet")
                break  # 退出菜单
            elif choice == "⚡ Magnet Environments":
                if self.adjust_magnet_environment():
                    break  # 如果选择了环境，退出主菜单
            elif choice == "🔧 Adjust Threshold (Interactive)":
                self.adjust_threshold()
            elif choice == "📏 Adjust Size (Interactive)":
                self.adjust_size()
            elif choice == "📐 Adjust Ratio (Interactive)":
                self.adjust_ratio()
            elif choice == "🎯 Toggle Capture Mode":
                self.send_command("toggle_capture")
            elif choice == "⏸️ Toggle Stop/Start":
                self.send_command("toggle_stop")
            elif choice == "🔄 Refresh Display":
                self.send_command("refresh")
            elif choice == "🖱️ Select Area (slop)":
                self.send_command("select_area")


def main():
    """主函数"""
    menu = EinkRofiMenu()

    # 检查应用是否运行
    if not menu.check_app_running():
        menu.rofi.show_error("E-ink app is not running or pipe not found!")
        sys.exit(1)

    # 运行主菜单
    menu.run_main_menu()


if __name__ == "__main__":
    main()
