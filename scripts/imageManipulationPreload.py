# Required pip installations:
# pip install pillow
# pip install tk

import os
import shutil
import json
import threading
from collections import deque
from tkinter import Tk, Button, Label, Listbox, Scrollbar, simpledialog, Canvas, NW
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk, ImageOps

class ImageViewer:
    def __init__(self, root):
        self.root = root
        self.settings_file = "settings.json"
        self.load_settings()
        self.root.title(f"Image Viewer and Manipulation - {os.path.basename(self.settings['source_folder'])}")

        self.image_list = []
        self.current_image_index = 0
        self.zoom_level = 1.0
        self.canvas_image_id = None

        self.cropping = False
        self.crop_rectangle = None
        self.crop_start_x = 0
        self.crop_start_y = 0

        self.undo_stack = deque(maxlen=10)  # Limit to last 10 actions

        self.image_cache = {}

        self.create_widgets()
        self.load_images()

    def load_settings(self):
        try:
            with open(self.settings_file, 'r') as file:
                self.settings = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.settings = {
                'source_folder': 'generated_images',
                'destination_folders': ['freckels', 'freckels/nsfw', 'generic']
            }
        self.save_settings()

    def save_settings(self):
        with open(self.settings_file, 'w') as file:
            json.dump(self.settings, file)

    def load_images(self):
        self.image_list = [f for f in os.listdir(self.settings['source_folder']) if os.path.isfile(os.path.join(self.settings['source_folder'], f))]
        self.current_image_index = 0
        self.load_image(self.current_image_index)
        self.start_preloading()

    def create_widgets(self):
        self.button_frame = ttk.Frame(self.root)
        self.button_frame.pack(side="top", fill="x", padx=5, pady=5)

        self.canvas_frame = ttk.Frame(self.root)
        self.canvas_frame.pack(side="left", fill="both", expand=True)
        
        self.canvas = Canvas(self.canvas_frame, cursor="cross")
        self.canvas.pack(fill="both", expand=True)
        
        self.status_bar = ttk.Label(self.canvas_frame, text="Zoom: 100%", relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

        self.dest_frame = ttk.Frame(self.root)
        self.dest_frame.pack(side="right", fill="y")

        self.dest_label = ttk.Label(self.dest_frame, text="Destination Folders:")
        self.dest_label.pack(side="top", anchor="n")

        self.dest_listbox = Listbox(self.dest_frame, selectmode='single')
        self.update_dest_listbox()
        self.dest_listbox.pack(side="top", fill="both", expand=True)

        self.dest_scroll = Scrollbar(self.dest_listbox, orient='vertical')
        self.dest_scroll.config(command=self.dest_listbox.yview)
        self.dest_listbox.config(yscrollcommand=self.dest_scroll.set)
        self.dest_scroll.pack(side='right', fill='y')

        self.add_dest_button = ttk.Button(self.dest_frame, text="Add Folder", command=self.add_folder)
        self.add_dest_button.pack(side="top")

        self.remove_dest_button = ttk.Button(self.dest_frame, text="Remove Folder", command=self.remove_folder)
        self.remove_dest_button.pack(side="top")

        self.buttons = [
            ("Load Images (L)", self.load_images),
            ("Change Source Folder", self.change_source_folder),
            ("Delete (Del)", self.delete_image),
            ("Previous (←)", self.show_prev_image),
            ("Next (→)", self.show_next_image),
            ("Zoom In (+)", lambda: self.zoom(1.1)),
            ("Zoom Out (-)", lambda: self.zoom(0.9)),
            ("Reset Zoom (R)", self.reset_zoom),
            ("Undo (Ctrl+Z)", self.undo)
        ]

        self.button_widgets = []
        for text, command, *state in self.buttons:
            button = ttk.Button(self.button_frame, text=text, command=command)
            if state:
                button.config(state=state[0])
            self.button_widgets.append(button)
            button.pack(side="left", padx=5, pady=5)

        self.root.bind("<Left>", lambda e: self.show_prev_image())
        self.root.bind("<Right>", lambda e: self.show_next_image())
        self.root.bind("<Delete>", lambda e: self.delete_image())
        self.root.bind("<Return>", lambda e: self.apply_crop())
        self.root.bind("<Escape>", lambda e: self.cancel_crop())
        self.root.bind("<Control-MouseWheel>", self.zoom_with_scroll)
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("+", lambda e: self.zoom(1.1))
        self.root.bind("-", lambda e: self.zoom(0.9))
        self.root.bind("r", lambda e: self.reset_zoom())
        self.canvas.bind("<MouseWheel>", self.zoom_with_scroll)
        self.canvas.bind("<Button-4>", self.zoom_with_scroll)  # For Linux
        self.canvas.bind("<Button-5>", self.zoom_with_scroll)  # For Linux
        self.canvas.bind("<Double-1>", self.start_cropping)  # Double-click to start crop
        self.canvas.bind("<Button-2>", self.finish_crop)  # Middle-click to finish crop
        self.dest_listbox.bind("<Double-1>", lambda e: self.move_image_to_folder())
        self.dest_listbox.bind("<<ListboxSelect>>", self.on_listbox_select)
        self.root.bind("<Key>", self.move_image_with_hotkey)
        self.canvas.bind("<ButtonPress-1>", self.start_pan_image)
        self.canvas.bind("<B1-Motion>", self.pan_image)

        self.root.bind("<Configure>", self.on_resize)

        # Initialize crop control buttons
        self.save_crop_button = ttk.Button(self.button_frame, text="Save Crop (Enter)", command=self.apply_crop, state='disabled')
        self.save_crop_button.pack(side="left", padx=5, pady=5)
        self.cancel_crop_button = ttk.Button(self.button_frame, text="Cancel Crop (Esc)", command=self.cancel_crop, state='disabled')
        self.cancel_crop_button.pack(side="left", padx=5, pady=5)
        self.crop_button = ttk.Button(self.button_frame, text="Crop (C)", command=self.start_cropping)
        self.crop_button.pack(side="left", padx=5, pady=5)
        self.button_widgets.extend([self.crop_button, self.save_crop_button, self.cancel_crop_button])

        self.rearrange_buttons()

    def on_resize(self, event):
        self.rearrange_buttons()

    def rearrange_buttons(self):
        button_frame_width = self.button_frame.winfo_width()
        x = 0
        y = 0
        max_height = 0

        for button in self.button_widgets:
            button_width = button.winfo_reqwidth()
            button_height = button.winfo_reqheight()

            if x + button_width > button_frame_width:
                x = 0
                y += max_height + 5
                max_height = 0

            button.place(x=x, y=y)
            x += button_width + 5
            max_height = max(max_height, button_height)

        self.button_frame.config(height=y + max_height + 5)

    def update_dest_listbox(self):
        self.dest_listbox.delete(0, 'end')
        folder_paths = self.settings['destination_folders']
        unique_names = self.get_unique_display_names(folder_paths)

        for i, folder in enumerate(folder_paths):
            self.dest_listbox.insert('end', f"{unique_names[i]} ({i + 1})")

    def get_unique_display_names(self, folder_paths):
        unique_names = [os.path.basename(folder) for folder in folder_paths]
        path_depths = [1] * len(folder_paths)

        def generate_unique_name(folder, depth):
            parts = folder.split(os.sep)
            return os.path.join(*parts[-depth:])

        while True:
            unique_name_map = {}
            for i, folder in enumerate(folder_paths):
                unique_name = generate_unique_name(folder, path_depths[i])
                if unique_name in unique_name_map:
                    unique_name_map[unique_name].append(i)
                else:
                    unique_name_map[unique_name] = [i]

            duplicates = {k: v for k, v in unique_name_map.items() if len(v) > 1}

            if not duplicates:
                break

            for indices in duplicates.values():
                for index in indices:
                    path_depths[index] += 1

        return [generate_unique_name(folder_paths[i], path_depths[i]) for i in range(len(folder_paths))]

    def on_listbox_select(self, event):
        widget = event.widget
        index = widget.curselection()
        if index:
            folder = self.settings['destination_folders'][index[0]]
            self.status_bar.config(text=f"Zoom: {self.zoom_level * 100:.0f}% | {folder} ({index[0] + 1})")

    def show_image(self):
        try:
            if not self.image_list:
                return
            image_name = self.image_list[self.current_image_index]
            self.status_bar.config(text=f"Zoom: {self.zoom_level * 100:.0f}% | {image_name}")
            if image_name in self.image_cache:
                self.display_image = self.image_cache[image_name]
            else:
                self.load_image(self.current_image_index)
            self.update_image()
            self.start_preloading()
        except Exception as e:
            self.handle_exception(e)

    def load_image(self, index):
        image_name = self.image_list[index]
        image_path = os.path.join(self.settings['source_folder'], image_name)
        self.original_image = Image.open(image_path)
        self.display_image = self.original_image.copy()
        self.image_cache[image_name] = self.display_image

    def update_image(self):
        try:
            img = ImageOps.scale(self.display_image, self.zoom_level)
            self.tk_img = ImageTk.PhotoImage(img)
            if self.canvas_image_id is not None:
                self.canvas.itemconfig(self.canvas_image_id, image=self.tk_img)
            else:
                self.canvas_image_id = self.canvas.create_image(0, 0, anchor=NW, image=self.tk_img)
            image_name = self.image_list[self.current_image_index]
            self.status_bar.config(text=f"Zoom: {self.zoom_level * 100:.0f}% | {image_name}")
        except Exception as e:
            self.handle_exception(e)

    def show_prev_image(self):
        try:
            if self.current_image_index > 0:
                self.current_image_index -= 1
                self.show_image()
        except Exception as e:
            self.handle_exception(e)

    def show_next_image(self):
        try:
            if self.current_image_index < len(self.image_list) - 1:
                self.current_image_index += 1
                self.show_image()
        except Exception as e:
            self.handle_exception(e)

    def start_cropping(self, event=None):
        try:
            if self.cropping:  # Check if we are already in crop mode
                return
            self.cropping = True
            self.save_crop_button.config(state='normal')
            self.cancel_crop_button.config(state='normal')
            self.crop_button.config(state='disabled')
            self.root.unbind("c")
            self.crop_rectangle = None
            self.canvas.bind("<Button-1>", self.start_crop_rectangle)
            self.canvas.bind("<B1-Motion>", self.draw_crop_rectangle)
            self.canvas.bind("<ButtonRelease-1>", self.finish_crop_rectangle)
        except Exception as e:
            self.handle_exception(e)

    def start_crop_rectangle(self, event):
        try:
            self.crop_start_x, self.crop_start_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
            if self.crop_rectangle:
                self.canvas.delete(self.crop_rectangle)
            self.crop_rectangle = self.canvas.create_rectangle(self.crop_start_x, self.crop_start_y, self.crop_start_x, self.crop_start_y, outline='red')
        except Exception as e:
            self.handle_exception(e)

    def draw_crop_rectangle(self, event):
        try:
            if self.crop_rectangle:
                self.canvas.coords(self.crop_rectangle, self.crop_start_x, self.crop_start_y, self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        except Exception as e:
            self.handle_exception(e)

    def finish_crop_rectangle(self, event):
        try:
            self.crop_end_x, self.crop_end_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        except Exception as e:
            self.handle_exception(e)

    def apply_crop(self):
        try:
            if not self.cropping or not self.crop_rectangle:
                return

            # Get current scroll position fractions
            xview_start, xview_end = self.canvas.xview()
            yview_start, yview_end = self.canvas.yview()

            # Calculate crop coordinates
            x1, y1, x2, y2 = self.canvas.coords(self.crop_rectangle)
            x1, y1, x2, y2 = int(x1 / self.zoom_level), int(y1 / self.zoom_level), int(x2 / self.zoom_level), int(y2 / self.zoom_level)

            self.undo_stack.append((self.display_image.copy(), "crop"))
            self.display_image = self.display_image.crop((x1, y1, x2, y2))
            self.original_image = self.display_image.copy()
            self.original_image.save(os.path.join(self.settings['source_folder'], self.image_list[self.current_image_index]))
            self.image_cache[self.image_list[self.current_image_index]] = self.display_image

            self.cancel_crop()

            # Update the image without resetting the zoom
            self.update_image()

            # Calculate the new scroll positions based on the cropped area
            new_width = x2 - x1
            new_height = y2 - y1

            new_xview_start = (xview_start * self.original_image.width - x1) / new_width
            new_yview_start = (yview_start * self.original_image.height - y1) / new_height

            self.canvas.xview_moveto(new_xview_start)
            self.canvas.yview_moveto(new_yview_start)

        except Exception as e:
            self.handle_exception(e)

    def finish_crop(self, event=None):
        try:
            self.apply_crop()
        except Exception as e:
            self.handle_exception(e)

    def cancel_crop(self):
        try:
            if self.cropping:
                self.cropping = False
                self.save_crop_button.config(state='disabled')
                self.cancel_crop_button.config(state='disabled')
                self.crop_button.config(state='normal')
                self.root.bind("c", lambda e: self.start_cropping())
                self.canvas.unbind("<Button-1>")
                self.canvas.unbind("<B1-Motion>")
                self.canvas.unbind("<ButtonRelease-1>")

                if self.crop_rectangle:
                    self.canvas.delete(self.crop_rectangle)
                    self.crop_rectangle = None

                # Rebind events for panning
                self.canvas.bind("<ButtonPress-1>", self.start_pan_image)
                self.canvas.bind("<B1-Motion>", self.pan_image)
        except Exception as e:
            self.handle_exception(e)

    def delete_image(self):
        try:
            image_name = self.image_list[self.current_image_index]
            self.undo_stack.append((self.original_image.copy(), "delete", image_name))
            os.remove(os.path.join(self.settings['source_folder'], image_name))
            del self.image_cache[image_name]
            del self.image_list[self.current_image_index]
            if self.current_image_index >= len(self.image_list):
                self.current_image_index -= 1
            self.show_image()
        except Exception as e:
            self.handle_exception(e)

    def add_folder(self):
        try:
            folder = filedialog.askdirectory(title="Select Destination Folder")
            if folder and folder not in self.settings['destination_folders']:
                self.settings['destination_folders'].append(folder)
                self.update_dest_listbox()
                self.save_settings()
        except Exception as e:
            self.handle_exception(e)

    def change_source_folder(self):
        try:
            folder = filedialog.askdirectory(title="Select Source Folder")
            if folder:
                self.settings['source_folder'] = folder
                self.save_settings()
                self.root.title(f"Image Viewer and Manipulation - {os.path.basename(self.settings['source_folder'])}")
                self.load_images()
        except Exception as e:
            self.handle_exception(e)

    def remove_folder(self):
        try:
            selected = self.dest_listbox.curselection()
            if selected:
                display_name = self.dest_listbox.get(selected).split(' ')[0]
                folder_to_remove = None
                for folder in self.settings['destination_folders']:
                    if folder.endswith(display_name):
                        folder_to_remove = folder
                        break
                if folder_to_remove:
                    self.settings['destination_folders'].remove(folder_to_remove)
                    self.update_dest_listbox()
                    self.save_settings()
        except Exception as e:
            self.handle_exception(e)

    def move_image_with_hotkey(self, event):
        try:
            if event.char.isdigit():
                index = int(event.char) - 1
                if 0 <= index < len(self.settings['destination_folders']):
                    folder = self.settings['destination_folders'][index]
                    self.move_image_to_folder(folder)
        except Exception as e:
            self.handle_exception(e)

    def move_image_to_folder(self, folder=None):
        try:
            if folder is None:
                selected = self.dest_listbox.curselection()
                if selected:
                    folder = self.settings['destination_folders'][selected[0]]
            if folder:
                src_path = os.path.join(self.settings['source_folder'], self.image_list[self.current_image_index])
                dest_path = os.path.join(folder, os.path.basename(src_path))
                self.undo_stack.append((src_path, "move", folder))
                shutil.move(src_path, dest_path)
                image_name = self.image_list[self.current_image_index]
                del self.image_cache[image_name]
                del self.image_list[self.current_image_index]
                if self.current_image_index >= len(self.image_list):
                    self.current_image_index -= 1
                self.show_image()
        except Exception as e:
            self.handle_exception(e)

    def undo(self):
        try:
            if not self.undo_stack:
                return
            last_action = self.undo_stack.pop()
            if last_action[1] == "crop":
                self.display_image = last_action[0]
                self.original_image = self.display_image.copy()
                self.original_image.save(os.path.join(self.settings['source_folder'], self.image_list[self.current_image_index]))
                self.image_cache[self.image_list[self.current_image_index]] = self.display_image
                self.update_image()
            elif last_action[1] == "delete":
                self.image_list.insert(self.current_image_index, last_action[2])
                last_action[0].save(os.path.join(self.settings['source_folder'], last_action[2]))
                self.image_cache[last_action[2]] = last_action[0]
                self.show_image()
            elif last_action[1] == "move":
                src_path, _, folder = last_action
                dest_path = os.path.join(folder, os.path.basename(src_path))
                shutil.move(dest_path, src_path)
                self.image_list.insert(self.current_image_index, os.path.basename(src_path))
                self.load_image(self.current_image_index)
                self.show_image()
        except Exception as e:
            self.handle_exception(e)

    def zoom(self, factor):
        try:
            self.zoom_level *= factor
            self.update_image()
        except Exception as e:
            self.handle_exception(e)

    def reset_zoom(self):
        try:
            self.zoom_level = 1.0
            self.canvas.xview_moveto(0)
            self.canvas.yview_moveto(0)
            self.update_image()
        except Exception as e:
            self.handle_exception(e)

    def zoom_with_scroll(self, event):
        try:
            if event.num == 4 or event.delta > 0:
                self.zoom(1.1)
            elif event.num == 5 or event.delta < 0:
                self.zoom(0.9)
        except Exception as e:
            self.handle_exception(e)

    def start_pan_image(self, event):
        try:
            self.canvas.scan_mark(event.x, event.y)
        except Exception as e:
            self.handle_exception(e)

    def pan_image(self, event):
        try:
            self.canvas.scan_dragto(event.x, event.y, gain=1)
        except Exception as e:
            self.handle_exception(e)

    def handle_exception(self, exception):
        self.status_bar.config(style="Error.TLabel")
        raise exception  # Re-raise the exception after handling

    def preload_images(self):
        for i in range(1, 11):
            index = (self.current_image_index + i) % len(self.image_list)
            image_name = self.image_list[index]
            if image_name not in self.image_cache:
                image_path = os.path.join(self.settings['source_folder'], image_name)
                try:
                    image = Image.open(image_path).copy()
                    self.image_cache[image_name] = image
                    if index == self.current_image_index:
                        self.display_image = image
                        self.update_image()
                except Exception as e:
                    self.handle_exception(e)

    def start_preloading(self):
        threading.Thread(target=self.preload_images, daemon=True).start()

if __name__ == "__main__":
    root = Tk()
    style = ttk.Style(root)
    style.configure("Error.TLabel", background="red")
    app = ImageViewer(root)
    root.mainloop()
