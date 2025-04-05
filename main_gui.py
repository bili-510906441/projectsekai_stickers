import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import psutil
import pyautogui

class PJSKStickerMakerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PJSK表情包生成器 v1.0")
        self.root.geometry("750x400")
        self.root.resizable(False, False)
        
        # 初始化路径
        self.image_dir = "./data/stickers"
        self.font_dir = "./data/fonts"
        
        # 初始化文件结构和变量
        self.characters = self.load_characters()
        self.font_files = self.load_fonts()
        
        self.original_image = None
        self.text_content = tk.StringVar()
        self.font_size = tk.IntVar(value=40)
        self.text_color = tk.StringVar(value='255,255,255')
        self.stroke_color = tk.StringVar(value='0,0,0')
        self.stroke_width = tk.IntVar(value=2)
        self.pos_x = tk.IntVar(value=0)
        self.pos_y = tk.IntVar(value=0)
        self.rotation_angle = tk.IntVar(value=0)
        self.memory_usage = tk.StringVar(value="内存使用: 计算中...")
        
        self.setup_ui()
        self.check_dependencies()
        self.start_memory_monitor()

    def load_characters(self):
        """加载角色分类"""
        characters = {}
        try:
            for filename in os.listdir(self.image_dir):
                if filename.endswith(".png"):
                    parts = filename[:-4].split("_")
                    if len(parts) >= 2 and len(parts[-1]) == 2 and parts[-1].isdigit():
                        char_name = "_".join(parts[:-1])
                        if char_name not in characters:
                            characters[char_name] = []
                        characters[char_name].append(parts[-1])
            for char in characters:
                characters[char].sort()
            return characters
        except Exception as e:
            self.show_error(f"加载图片失败: {str(e)}")
            return {}

    def load_fonts(self):
        """加载字体文件"""
        try:
            return [f for f in os.listdir(self.font_dir) if f.endswith(".ttf")]
        except Exception as e:
            self.show_error(f"加载字体失败: {str(e)}")
            return []

    def check_dependencies(self):
        """检查依赖文件"""
        errors = []
        if not self.characters:
            errors.append(f"{self.image_dir} 中没有有效图片")
        if not self.font_files:
            errors.append(f"{self.font_dir} 中没有TTF字体")
        if errors:
            self.show_error("\n".join(errors))
            self.root.destroy()

    def setup_ui(self):
        """界面布局"""
        # 控制面板
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.grid(row=0, column=0, sticky=tk.NSEW)
        
        # 配置网格布局权重
        control_frame.columnconfigure(1, weight=1)
        control_frame.columnconfigure(2, minsize=10)  # 操作按钮间隙
        
        # 统一控件参数
        padx_default = 5
        pady_default = 3
        entry_width = 20
        
        # 角色选择
        row = 0
        ttk.Label(control_frame, text="角色:").grid(
            row=row, column=0, padx=padx_default, pady=pady_default, sticky=tk.W)
        self.char_combo = ttk.Combobox(control_frame, state="readonly", width=entry_width-2)
        self.char_combo.grid(row=row, column=1, padx=padx_default, pady=pady_default, sticky=tk.EW)
        self.char_combo.bind("<<ComboboxSelected>>", self.update_numbers)
        
        # 编号选择
        row += 1
        ttk.Label(control_frame, text="编号:").grid(
            row=row, column=0, padx=padx_default, pady=pady_default, sticky=tk.W)
        self.num_combo = ttk.Combobox(control_frame, state="readonly", width=entry_width-2)
        self.num_combo.grid(row=row, column=1, padx=padx_default, pady=pady_default, sticky=tk.EW)
        self.num_combo.bind("<<ComboboxSelected>>", self.load_image)
        
        # 字体选择
        row += 1
        ttk.Label(control_frame, text="字体:").grid(
            row=row, column=0, padx=padx_default, pady=pady_default, sticky=tk.W)
        self.font_combo = ttk.Combobox(control_frame, values=self.font_files, 
                                    state="readonly", width=entry_width)
        self.font_combo.grid(row=row, column=1, padx=padx_default, pady=pady_default, sticky=tk.EW)
        
        # 文字内容
        row += 1
        ttk.Label(control_frame, text="内容:").grid(
            row=row, column=0, padx=padx_default, pady=pady_default, sticky=tk.W)
        ttk.Entry(control_frame, textvariable=self.text_content, width=entry_width).grid(
            row=row, column=1, padx=padx_default, pady=pady_default, sticky=tk.EW)
        
        # 字体大小
        row += 1
        ttk.Label(control_frame, text="字号:").grid(
            row=row, column=0, padx=padx_default, pady=pady_default, sticky=tk.W)
        ttk.Spinbox(control_frame, from_=10, to=100, textvariable=self.font_size, 
                width=entry_width-5).grid(
                row=row, column=1, padx=padx_default, pady=pady_default, sticky=tk.W)
        
        # 文字颜色
        row += 1
        color_frame = ttk.Frame(control_frame)
        ttk.Label(control_frame, text="文字颜色:").grid(
            row=row, column=0, padx=padx_default, pady=pady_default, sticky=tk.W)
        color_frame.grid(row=row, column=1, padx=padx_default, pady=pady_default, sticky=tk.EW)
        self.color_preview = ttk.Label(color_frame, width=5, background='#FFFFFF')
        self.color_preview.pack(side=tk.LEFT)
        ttk.Entry(color_frame, textvariable=self.text_color, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(color_frame, text="取色", 
                command=lambda: self.start_color_pick(self.text_color)).pack(side=tk.LEFT)
        
        # 描边设置
        row += 1
        stroke_frame = ttk.Frame(control_frame)
        ttk.Label(control_frame, text="描边设置:").grid(
            row=row, column=0, padx=padx_default, pady=pady_default, sticky=tk.W)
        stroke_frame.grid(row=row, column=1, padx=padx_default, pady=pady_default, sticky=tk.EW)
        ttk.Entry(stroke_frame, textvariable=self.stroke_color, width=10).pack(side=tk.LEFT)
        ttk.Button(stroke_frame, text="取色", 
                command=lambda: self.start_color_pick(self.stroke_color)).pack(side=tk.LEFT, padx=2)
        ttk.Spinbox(stroke_frame, from_=0, to=10, textvariable=self.stroke_width, 
                width=4).pack(side=tk.LEFT)
        
        # 旋转角度
        row += 1
        ttk.Label(control_frame, text="旋转角度:").grid(
            row=row, column=0, padx=padx_default, pady=pady_default, sticky=tk.W)
        ttk.Spinbox(control_frame, from_=0, to=360, textvariable=self.rotation_angle, 
                width=entry_width-5).grid(
                row=row, column=1, padx=padx_default, pady=pady_default, sticky=tk.W)
        
        # 位置设置 (修改后)
        row += 1
        pos_frame = ttk.Frame(control_frame)
        ttk.Label(control_frame, text="位置 (X,Y):").grid(
            row=row, column=0, padx=padx_default, pady=pady_default, sticky=tk.W)
        pos_frame.grid(row=row, column=1, padx=padx_default, pady=pady_default, sticky=tk.W)
        ttk.Entry(pos_frame, textvariable=self.pos_x, width=5).pack(side=tk.LEFT)
        ttk.Label(pos_frame, text=",").pack(side=tk.LEFT)
        ttk.Entry(pos_frame, textvariable=self.pos_y, width=5).pack(side=tk.LEFT)

        # 操作按钮
        row += 1
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=10, sticky=tk.EW)

        # 定位按钮整合到操作区域
        ttk.Button(btn_frame, text="定位", 
                command=self.enable_position_pick).pack(side=tk.LEFT, expand=True, padx=2)
        ttk.Button(btn_frame, text="预览", 
                command=self.update_preview).pack(side=tk.LEFT, expand=True, padx=2)
        ttk.Button(btn_frame, text="导出", 
                command=self.export_image).pack(side=tk.LEFT, expand=True, padx=2)
        
        # 状态标签
        row += 1
        self.status_label = ttk.Label(control_frame, foreground='red')
        self.status_label.grid(row=row, column=0, columnspan=3, sticky=tk.EW)
        
        # 预览区域
        self.preview_label = ttk.Label(self.root)
        self.preview_label.grid(row=0, column=1, padx=10, pady=10, sticky=tk.NSEW)
        self.preview_label.bind("<Button-1>", self.on_preview_click)
        
        # 内存显示
        ttk.Label(self.root, textvariable=self.memory_usage).grid(row=1, column=1, sticky=tk.SE, padx=10)
        
        # 初始化下拉框
        self.char_combo["values"] = sorted(self.characters.keys())
        self.font_combo["values"] = self.font_files
        
        # 布局配置
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        
    def start_memory_monitor(self):
        """启动内存监控"""
        self.process = psutil.Process(os.getpid())
        self.update_memory_usage()

    def update_memory_usage(self):
        try:
            mem = self.process.memory_info().rss / 1024 / 1024
            self.memory_usage.set(f"内存使用: {mem:.2f} MB")
        except Exception as e:
            self.memory_usage.set("内存监控错误")
        finally:
            self.root.after(2000, self.update_memory_usage)

    def update_numbers(self, event=None):
        """更新编号列表"""
        char = self.char_combo.get()
        self.num_combo["values"] = self.characters.get(char, [])
        self.num_combo.set("")

    def load_image(self, event=None):
        """加载图片"""
        char = self.char_combo.get()
        num = self.num_combo.get()
        if char and num:
            try:
                path = os.path.join(self.image_dir, f"{char}_{num}.png")
                self.original_image = Image.open(path)
                self.update_preview()
            except Exception as e:
                self.show_error(f"加载图片失败: {str(e)}")

    def enable_position_pick(self):
        """启用坐标选择"""
        messagebox.showinfo("提示", "点击预览图片设置坐标")

    def start_color_pick(self, target_var):
        """启动颜色选择"""
        self.pick_color_target = target_var
        self.status_label.config(text="请在屏幕上移动鼠标选择颜色，左键确认/右键取消")
        self.root.config(cursor="crosshair")
        self.root.bind("<Motion>", self.update_color_preview)
        self.root.bind("<Button-1>", self.finalize_color_pick)
        self.root.bind("<Button-3>", self.cancel_color_pick)

    def update_color_preview(self, event):
        """实时更新颜色预览"""
        try:
            x, y = event.x_root, event.y_root  # 获取屏幕坐标
            im = pyautogui.screenshot()
            r, g, b = im.getpixel((x, y))
            hex_color = f'#{r:02x}{g:02x}{b:02x}'
            self.color_preview.config(background=hex_color)
        except Exception as e:
            self.show_error(f"颜色预览失败: {str(e)}")

    def finalize_color_pick(self, event):
        """确认颜色选择"""
        try:
            x, y = event.x_root, event.y_root
            im = pyautogui.screenshot()
            r, g, b = im.getpixel((x, y))
            self.pick_color_target.set(f"{r},{g},{b}")
        finally:
            self.cleanup_color_pick()

    def cancel_color_pick(self, event):
        """取消颜色选择"""
        self.cleanup_color_pick()

    def cleanup_color_pick(self):
        """清理颜色选择状态"""
        self.status_label.config(text="")
        self.root.config(cursor="")
        self.root.unbind("<Motion>")
        self.root.unbind("<Button-1>")
        self.root.unbind("<Button-3>")
        self.color_preview.config(background='#FFFFFF')
    def on_preview_click(self, event):
        """处理预览点击事件"""
        if self.original_image:
            try:
                scale = self.original_image.width / self.preview_label.winfo_width()
                self.pos_x.set(int(event.x * scale))
                self.pos_y.set(int(event.y * scale))
                self.update_preview()
            except Exception as e:
                self.show_error(f"坐标转换失败: {str(e)}")

    def parse_color(self, color_str):
        """解析颜色值"""
        try:
            parts = list(map(int, color_str.split(",")))
            if len(parts) == 3 and all(0 <= p <= 255 for p in parts):
                return tuple(parts)
            raise ValueError
        except:
            return None

    def validate_inputs(self):
        """验证输入有效性"""
        errors = []
        if not self.char_combo.get() or not self.num_combo.get():
            errors.append("请选择角色和编号")
        if not self.font_combo.get():
            errors.append("请选择字体")
        if not self.text_content.get():
            errors.append("请输入文字内容")
        if not self.parse_color(self.text_color.get()):
            errors.append("无效的文字颜色格式(R,G,B)")
        if not self.parse_color(self.stroke_color.get()):
            errors.append("无效的描边颜色格式(R,G,B)")
        if self.stroke_width.get() < 0:
            errors.append("描边宽度不能为负数")
        if errors:
            self.show_error("\n".join(errors))
            return False
        return True

    def update_preview(self):
        """更新预览"""
        if not self.validate_inputs():
            return
        
        try:
            img = self.original_image.copy()
            draw = ImageDraw.Draw(img)
            
            # 解析参数
            text_color = self.parse_color(self.text_color.get())
            stroke_color = self.parse_color(self.stroke_color.get())
            font_path = os.path.join(self.font_dir, self.font_combo.get())
            font = ImageFont.truetype(font_path, self.font_size.get())
            stroke_width = self.stroke_width.get()
            
            # 创建旋转文本
            text = self.text_content.get()
            text_layer = Image.new("RGBA", img.size, (0,0,0,0))
            text_draw = ImageDraw.Draw(text_layer)
            
            # 计算位置
            x, y = self.pos_x.get(), self.pos_y.get()
            
            # 绘制文本
            text_draw.text(
                (x, y), text,
                font=font,
                fill=text_color,
                stroke_width=stroke_width,
                stroke_fill=stroke_color
            )
            rotated = text_layer.rotate(
                self.rotation_angle.get(),
                center=(x, y),
                expand=True
            )
            
            # 合并图层
            img.paste(rotated, (0, 0), rotated)
            
            # 生成预览
            preview = img.copy()
            preview.thumbnail((600, 600))
            border_draw = ImageDraw.Draw(preview)
            border_draw.rectangle([0, 0, preview.width-1, preview.height-1], outline="red", width=1)
            
            # 更新显示
            self.preview_img = ImageTk.PhotoImage(preview)
            self.preview_label.config(image=self.preview_img)
            
        except Exception as e:
            self.show_error(f"生成预览失败: {str(e)}")

    def export_image(self):
        """导出图片"""
        if not self.validate_inputs():
            return
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG文件", "*.png"), ("JPEG文件", "*.jpg")]
        )
        if not save_path:
            return
        
        try:
            img = self.original_image.copy()
            draw = ImageDraw.Draw(img)
            
            text_color = self.parse_color(self.text_color.get())
            stroke_color = self.parse_color(self.stroke_color.get())
            font_path = os.path.join(self.font_dir, self.font_combo.get())
            font = ImageFont.truetype(font_path, self.font_size.get())
            
            text = self.text_content.get()
            text_layer = Image.new("RGBA", img.size, (0,0,0,0))
            text_draw = ImageDraw.Draw(text_layer)
            
            x, y = self.pos_x.get(), self.pos_y.get()
            
            text_draw.text(
                (x, y), text,
                font=font,
                fill=text_color,
                stroke_width=self.stroke_width.get(),
                stroke_fill=stroke_color
            )
            rotated = text_layer.rotate(
                self.rotation_angle.get(),
                center=(x, y),
                expand=True
            )
            
            img.paste(rotated, (0, 0), rotated)
            img.save(save_path)
            messagebox.showinfo("成功", "文件保存成功！")
            
        except Exception as e:
            self.show_error(f"保存失败: {str(e)}")

    def show_error(self, message):
        """显示错误信息"""
        messagebox.showerror("错误", message)

if __name__ == "__main__":
    root = tk.Tk()
    try:
        app = PJSKStickerMakerApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("致命错误", f"程序崩溃: {str(e)}")
