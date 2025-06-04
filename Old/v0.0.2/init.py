# Optimized AgentExecutive - Tkinter Version with Thonny
# Requirements: selenium, openai, flask, tkinter, threading

import os
import openai
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image, ImageTk
import json
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, filedialog, Frame

# Helper Class for LLM Integration
class LLMHandler:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_llm_action(self, snapshot, role, goal):
        openai.api_key = self.api_key
        system_prompt = f"You are acting as: {role}. Your goal is: {goal}. Based on the given webpage snapshot, return the next action in JSON format."
        response = openai.Completion.create(
            engine="gpt-3.5-turbo",
            prompt=f"{system_prompt}\nWebpage Snapshot: {snapshot}\nReturn only the JSON format with the action. No other text.",
            max_tokens=100,
            temperature=0.7
        )
        try:
            return json.loads(response.choices[0].text.strip())
        except json.JSONDecodeError:
            return {"type": "ERROR", "message": "Invalid JSON response from LLM."}

# Selenium Automation Setup with Improvements
class WebPageHandler:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run headless for simplicity
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def load_page(self, url):
        try:
            self.driver.get(url)
            time.sleep(2)  # wait for the page to load fully
            return "success"
        except Exception as e:
            return f"failure: {str(e)}"

    def get_snapshot(self):
        # Getting a basic snapshot including buttons, inputs, etc.
        elements = self.driver.find_elements(By.XPATH, "//button | //input | //a")
        snapshot = {
            "html_preview": self.driver.page_source[:500],
            "elements": [
                {
                    "tag": element.tag_name,
                    "text": element.text,
                    "xpath": self.get_element_xpath(element)
                } for element in elements
            ]
        }
        return json.dumps(snapshot)

    def perform_action(self, action):
        try:
            if action['type'] == 'CLICK':
                element = self.driver.find_element(By.XPATH, action['target'])
                element.click()
            elif action['type'] == 'SCROLL':
                element = self.driver.find_element(By.XPATH, action['target'])
                self.driver.execute_script("arguments[0].scrollIntoView();", element)
            time.sleep(1)
            return "success"
        except Exception as e:
            return f"failure: {str(e)}"

    def take_screenshot(self, filename="snapshot.png"):
        self.driver.save_screenshot(filename)

    @staticmethod
    def get_element_xpath(element):
        components = []
        child = element if element else None
        while child is not None:
            parent = child.find_element(By.XPATH, "..")
            siblings = parent.find_elements(By.XPATH, f"./{child.tag_name}")
            components.append(
                f"{child.tag_name}[{siblings.index(child) + 1}]" if len(siblings) > 1 else child.tag_name
            )
            child = parent
        components.reverse()
        return f"/{'/'.join(components)}"

# Threaded Function for Background Tasks
def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper

# Tkinter GUI Setup with Helper Classes and Threading
class AssistantSession:
    def __init__(self, url, role, goal):
        self.url = url
        self.role = role
        self.goal = goal
        self.actions = []
        self.logs = []

class AgentExecutiveApp:
    def __init__(self, root):
        self.root = root
        root.title("AgentExecutive - Optimized Version")
        root.geometry("1200x900")

        self.web_handler = WebPageHandler()
        self.llm_handler = LLMHandler(os.getenv("OPENAI_API_KEY"))

        # Main Menu
        self.main_menu = tk.Menu(root)
        root.config(menu=self.main_menu)
        file_menu = tk.Menu(self.main_menu, tearoff=0)
        file_menu.add_command(label="New", command=self.new_execution)
        file_menu.add_command(label="Save execution", command=self.save_execution)
        file_menu.add_command(label="Load execution", command=self.load_execution)
        file_menu.add_command(label="Logs", command=self.show_logs)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_application)
        self.main_menu.add_cascade(label="File", menu=file_menu)

        # Assistants Tabs
        self.tab_control = ttk.Notebook(root)
        self.add_new_tab()
        self.tab_control.pack(expand=1, fill="both")

        # Add close button on each tab
        self.tab_control.bind("<Button-1>", self.tab_click_handler)

    def add_new_tab(self):
        new_tab = Frame(self.tab_control)
        tab_title = f"Assistant #{len(self.tab_control.tabs()) + 1}"
        self.tab_control.add(new_tab, text=tab_title)
        self.setup_tab_content(new_tab)
        self.add_close_button(tab_title)

    def setup_tab_content(self, tab):
        # URL Input
        url_label = tk.Label(tab, text="URL:")
        url_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        url_input = tk.Entry(tab, width=80)
        url_input.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        load_button = tk.Button(tab, text="Go", command=lambda: self.threaded_load_url(url_input, tab))
        load_button.grid(row=0, column=2, padx=5, pady=5)
        tab.url_input = url_input

        # Role and Goal Input
        role_label = tk.Label(tab, text="Role:")
        role_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')
        role_input = tk.Entry(tab, width=40)
        role_input.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        tab.role_input = role_input

        goal_label = tk.Label(tab, text="Goal:")
        goal_label.grid(row=2, column=0, padx=5, pady=5, sticky='w')
        goal_input = tk.Entry(tab, width=40)
        goal_input.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        tab.goal_input = goal_input

        # Fulfill Goal Button
        fulfill_button = tk.Button(tab, text="Fulfill goal/Stop execution", command=lambda: self.threaded_execute_step(role_input, goal_input, tab), width=30)
        fulfill_button.grid(row=3, column=1, padx=5, pady=10)

        # Screenshot Miniature
        screenshot_label = tk.Label(tab, text="Miniature of loaded webpage:")
        screenshot_label.grid(row=4, column=0, padx=5, pady=5, sticky='w')
        screenshot_canvas = tk.Label(tab)
        screenshot_canvas.grid(row=4, column=1, padx=5, pady=5, sticky='w')
        tab.screenshot_canvas = screenshot_canvas

        # Action and Status Fields
        next_action_label = tk.Label(tab, text="Next action:")
        next_action_label.grid(row=5, column=0, padx=5, pady=5, sticky='w')
        next_action_field = tk.Entry(tab, width=80)
        next_action_field.grid(row=5, column=1, padx=5, pady=5, sticky='w')
        tab.next_action_field = next_action_field

        previous_actions_label = tk.Label(tab, text="Previous actions:")
        previous_actions_label.grid(row=6, column=0, padx=5, pady=5, sticky='nw')
        previous_actions_list = scrolledtext.ScrolledText(tab, width=60, height=10, wrap=tk.WORD)
        previous_actions_list.grid(row=6, column=1, padx=5, pady=5, sticky='w')
        previous_actions_list.config(state=tk.DISABLED)
        tab.previous_actions_list = previous_actions_list

        # LLM JSON Output and Log Fields
        json_output_label = tk.Label(tab, text="LLM JSON output:")
        json_output_label.grid(row=7, column=0, padx=5, pady=5, sticky='w')
        json_output_field = scrolledtext.ScrolledText(tab, width=60, height=5, wrap=tk.WORD)
        json_output_field.grid(row=7, column=1, padx=5, pady=5, sticky='w')
        json_output_field.config(state=tk.DISABLED)
        tab.json_output_field = json_output_field

        log_label = tk.Label(tab, text="AgentExecutive log:")
        log_label.grid(row=8, column=0, padx=5, pady=5, sticky='w')
        log_field = scrolledtext.ScrolledText(tab, width=60, height=5, wrap=tk.WORD)
        log_field.grid(row=8, column=1, padx=5, pady=5, sticky='w')
        log_field.config(state=tk.DISABLED)
        tab.log_field = log_field

    @threaded
    def threaded_load_url(self, url_input, tab):
        url = url_input.get()
        if not url:
            messagebox.showerror("Input Error", "Please enter a valid URL before proceeding.")
            return
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        status = self.web_handler.load_page(url)
        if status == "success":
            self.web_handler.take_screenshot()
            self.append_status(tab.log_field, f"Loaded URL: {url}\nPage snapshot taken.")
            self.update_screenshot(tab)
        else:
            self.append_status(tab.log_field, f"Failed to load URL: {url}. Error: {status}")

    @threaded
    def threaded_execute_step(self, role_input, goal_input, tab):
        role = role_input.get()
        goal = goal_input.get()
        snapshot = self.web_handler.get_snapshot()
        action = self.llm_handler.get_llm_action(snapshot, role, goal)
        if action.get('type') == 'ERROR':
            self.append_status(tab.log_field, f"LLM Error: {action['message']}")
            return
        action_status = self.web_handler.perform_action(action)
        self.append_status(tab.log_field, f"Executed action: {json.dumps(action)}\nStatus: {action_status}")
        if action_status == 'success':
            self.web_handler.take_screenshot()
            self.update_screenshot(tab)
            self.append_status(tab.log_field, "Page snapshot updated.")
        tab.previous_actions_list.config(state=tk.NORMAL)
        tab.previous_actions_list.insert(tk.END, f"{json.dumps(action)} - {action_status}\n")
        tab.previous_actions_list.config(state=tk.DISABLED)

    def append_status(self, log_field, message):
        log_field.config(state=tk.NORMAL)
        log_field.insert(tk.END, message + "\n")
        log_field.config(state=tk.DISABLED)

    def update_screenshot(self, tab):
        try:
            image = Image.open("snapshot.png")
            image = image.resize((300, 200), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            tab.screenshot_canvas.config(image=photo)
            tab.screenshot_canvas.image = photo
        except Exception as e:
            self.append_status(tab.log_field, f"Error loading screenshot: {e}")

    # Placeholder methods for File Menu options
    def new_execution(self):
        # Add a new empty tab instead of clearing fields in the current tab
        self.add_new_tab()
        self.append_status(self.tab_control.nametowidget(self.tab_control.select()).log_field, "New tab added for new execution.")

    def save_execution(self):
        # Save the current state to a file
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if file_path:
            current_tab = self.tab_control.nametowidget(self.tab_control.select())
            data = {
                "url": current_tab.url_input.get(),
                "role": current_tab.role_input.get(),
                "goal": current_tab.goal_input.get()
            }
            with open(file_path, "w") as f:
                json.dump(data, f)
            self.append_status(current_tab.log_field, f"Execution saved to {file_path}.")

    def load_execution(self):
        # Load a state from a file
        file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if file_path:
            current_tab = self.tab_control.nametowidget(self.tab_control.select())
            with open(file_path, "r") as f:
                data = json.load(f)
            current_tab.url_input.delete(0, tk.END)
            current_tab.url_input.insert(0, data.get("url", ""))
            current_tab.role_input.delete(0, tk.END)
            current_tab.role_input.insert(0, data.get("role", ""))
            current_tab.goal_input.delete(0, tk.END)
            current_tab.goal_input.insert(0, data.get("goal", ""))
            self.append_status(current_tab.log_field, f"Execution loaded from {file_path}.")

    def show_logs(self):
        current_tab = self.tab_control.nametowidget(self.tab_control.select())
        self.append_status(current_tab.log_field, "Showing logs.")

    def exit_application(self):
        self.root.destroy()

    def tab_click_handler(self, event):
        # Handle clicking on a tab
        x, y, widget = event.x, event.y, event.widget
        if isinstance(widget, ttk.Notebook):
            tab_index = widget.index("@%d,%d" % (x, y))
            tab_bbox = widget.bbox(tab_index)
            if tab_bbox and (x > tab_bbox[2] - 20):
                # Click was on the close button area
                self.close_tab(tab_index)
            else:
                # Otherwise, switch to the tab
                widget.select(tab_index)

    def close_tab(self, tab_index):
        # Close the specified tab
        current_tab = self.tab_control.nametowidget(self.tab_control.tabs()[tab_index])
        if len(self.tab_control.tabs()) > 1:
            if messagebox.askyesno("Save Changes", "Do you want to save changes before closing?"):
                self.save_execution()
            self.tab_control.forget(tab_index)

    def add_close_button(self, tab_title):
        # Update tab title to include a close indicator (e.g., '✖')
        current_tab_index = len(self.tab_control.tabs()) - 1
        self.tab_control.tab(current_tab_index, text=f"{tab_title} ✖")

# Running the Application
def main():
    root = tk.Tk()
    app = AgentExecutiveApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
