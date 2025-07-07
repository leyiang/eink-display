#!/usr/bin/env python

import subprocess
from typing import Optional, List, Dict, Any


class RofiHelper:
    """Rofi调用帮助器 - 提供各种rofi界面功能"""
    
    def __init__(self):
        self.default_theme_str = 'entry { placeholder: "Test"; placeholder-color: grey; }'
    
    def show_error(self, message: str) -> None:
        """显示错误消息"""
        try:
            subprocess.run(['rofi', '-e', message], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error showing rofi error: {e}")
    
    def show_dmenu(self, 
                   options: List[str], 
                   prompt: str = "", 
                   selected_row: Optional[int] = None,
                   case_insensitive: bool = True,
                   use_old_rofi: bool = False,
                   theme_str: Optional[str] = None) -> Optional[str]:
        """
        显示rofi dmenu
        
        Args:
            options: 选项列表
            prompt: 提示文本
            selected_row: 默认选中的行（从0开始）
            case_insensitive: 是否不区分大小写
            use_old_rofi: 是否使用rofi_old命令
            theme_str: 自定义主题字符串
            
        Returns:
            用户选择的选项，如果取消则返回None
        """
        try:
            cmd = ['rofi_old' if use_old_rofi else 'rofi', '-dmenu']
            
            if case_insensitive:
                cmd.append('-i')
            
            if prompt:
                cmd.extend(['-p', prompt])
            
            if selected_row is not None:
                cmd.extend(['-selected-row', str(selected_row)])
            
            if theme_str:
                cmd.extend(['-theme-str', theme_str])
            elif use_old_rofi:
                cmd.extend(['-theme-str', self.default_theme_str])
            
            # 准备输入数据
            input_data = '\n'.join(options)
            
            result = subprocess.run(
                cmd,
                input=input_data,
                text=True,
                capture_output=True,
                check=False
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return None  # 用户取消或出错
                
        except Exception as e:
            print(f"Error running rofi: {e}")
            return None
    
    def show_interactive_menu(self, 
                            options: List[str], 
                            selected_row: int = 0,
                            prompt: str = "") -> Optional[str]:
        """显示交互式菜单（使用rofi_old）"""
        return self.show_dmenu(
            options=options,
            prompt=prompt,
            selected_row=selected_row,
            use_old_rofi=True,
            theme_str=self.default_theme_str
        )
    
    def show_main_menu(self, 
                      options: List[str], 
                      prompt: str = "E-ink Settings") -> Optional[str]:
        """显示主菜单"""
        return self.show_dmenu(
            options=options,
            prompt=prompt,
            use_old_rofi=False
        )
    
    def confirm_dialog(self, message: str, 
                      yes_text: str = "Yes", 
                      no_text: str = "No") -> bool:
        """显示确认对话框"""
        options = [yes_text, no_text]
        choice = self.show_dmenu(options, prompt=message)
        return choice == yes_text if choice else False