#!/usr/bin/env python

import os
import time
import select
import threading


class PipeManager:
    """管道通信管理器 - 处理命名管道的创建、监听和状态反馈"""

    def __init__(self, command_path="/tmp/eink_control", status_path="/tmp/eink_status"):
        self.command_path = command_path
        self.status_path = status_path
        self.command_handlers = {}
        self._listening = False
        self._listener_thread = None

    def create_pipes(self):
        """创建命名管道"""
        # Clean up existing pipes
        if os.path.exists(self.command_path):
            os.unlink(self.command_path)
        if os.path.exists(self.status_path):
            os.unlink(self.status_path)

        # Create new pipes
        os.mkfifo(self.command_path)
        os.mkfifo(self.status_path)
        print(f"Created command pipe: {self.command_path}")
        print(f"Created status pipe: {self.status_path}")

    def cleanup_pipes(self):
        """清理命名管道"""
        if os.path.exists(self.command_path):
            os.unlink(self.command_path)
        if os.path.exists(self.status_path):
            os.unlink(self.status_path)
        print("Cleaned up pipes")

    def register_command(self, command, handler):
        """注册命令处理器"""
        self.command_handlers[command] = handler

    def register_commands(self, command_dict):
        """批量注册命令处理器"""
        self.command_handlers.update(command_dict)

    def write_status(self, status):
        """写入状态信息到状态管道（非阻塞）"""
        try:
            # Use non-blocking write to avoid hanging if no reader
            fd = os.open(self.status_path, os.O_WRONLY | os.O_NONBLOCK)
            os.write(fd, (status + '\n').encode('utf-8'))
            os.close(fd)
        except OSError as e:
            if e.errno == 32:  # EPIPE - broken pipe (no reader)
                pass  # Silently ignore if no reader is waiting
            elif e.errno == 11:  # EAGAIN - would block
                pass  # Silently ignore if would block
            else:
                print(f"Error writing status: {e}")
        except Exception as e:
            print(f"Error writing status: {e}")

    def process_command(self, command):
        """处理接收到的命令"""
        print(f"Received command: {command}")
        if command in self.command_handlers:
            try:
                self.command_handlers[command]()
            except Exception as e:
                print(f"Error executing command '{command}': {e}")
        else:
            print(f"Unknown command: {command}")

    def listen_for_commands(self):
        """监听来自命名管道的命令"""
        pipe_fd = None
        try:
            # Open pipe once outside the loop
            pipe_fd = os.open(self.command_path, os.O_RDONLY | os.O_NONBLOCK)
            print(f"Opened pipe for listening: {self.command_path}")

            while self._listening:
                try:
                    # Use select to check if data is available
                    ready, _, _ = select.select([pipe_fd], [], [], 0.1)
                    if ready:
                        data = os.read(pipe_fd, 1024).decode('utf-8')
                        if data:
                            # Process each line as a separate command
                            for line in data.strip().split('\n'):
                                command = line.strip()
                                if command:
                                    self.process_command(command)
                    time.sleep(0.01)  # Very short sleep for responsiveness

                except OSError as e:
                    if e.errno == 11:  # EAGAIN - no data available
                        time.sleep(0.1)
                        continue
                    else:
                        raise e

        except Exception as e:
            print(f"Error in command listener: {e}")
        finally:
            if pipe_fd is not None:
                try:
                    os.close(pipe_fd)
                    print("Closed command pipe")
                except:
                    pass

    def start_listening(self):
        """开始监听命令（在独立线程中）"""
        if not self._listening:
            self._listening = True
            self._listener_thread = threading.Thread(target=self.listen_for_commands, daemon=True)
            self._listener_thread.start()
            print("Started command listener thread")

    def stop_listening(self):
        """停止监听命令"""
        if self._listening:
            self._listening = False
            if self._listener_thread:
                self._listener_thread.join(timeout=1)
            print("Stopped command listener")