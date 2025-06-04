# Optimized AgentExecutive - Tkinter Version
# Requirements: selenium, openai, Pillow, webdriver_manager

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

def threaded(fn):
    """
    Decorator voor het uitvoeren van functies in een aparte thread.
    """
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

class LLMHandler:
    """Handler voor LLM interacties"""
    def __init__(self, api_key):
        self.api_key = api_key

    def get_llm_action(self, snapshot, role, goal):
        """Verkrijg volgende actie van LLM"""
        openai.api_key = self.api_key
        system_prompt = f"""Je bent een {role}. Je doel is: {goal}. 
        Analyseer de webpagina snapshot en geef de volgende actie in JSON formaat.
        Alleen JSON terugsturen met formaat:
        {{
            "type": "CLICK/SCROLL/INPUT",
            "target": "xpath",
            "value": "waarde bij INPUT",
            "reasoning": "waarom deze actie"
        }}"""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Webpage Snapshot: {snapshot}"}
                ],
                temperature=0.7
            )
            return json.loads(response.choices[0].message.content.strip())
        except Exception as e:
            return {"type": "ERROR", "message": f"LLM Error: {str(e)}"}

class WebPageHandler:
    """Handler voor webpagina interacties"""
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
    def clean_url(url):
        """
        Schoont een URL op en valideert het formaat.
        Returns: (cleaned_url, error_message)
        """
        if not url:
            return None, "Please enter a URL"
            
        # Strip whitespace
        url = url.strip()
        
        # Remove common prefixes if present
        if url.startswith(("http://www.", "https://www.")):
            url = url.replace("www.", "", 1)
        elif url.startswith("www."):
            url = url.replace("www.", "", 1)
            url = "https://" + url
        elif not url.startswith(("http://", "https://")):
            url = "https://" + url
            
        # Basic validation (kan uitgebreid worden)
        if len(url) < 4 or "." not in url:
            return None, "Invalid URL format"
            
        return url, None
    
    @threaded
    def load_url(self, url, tab):
        """Laad een URL en update de UI met verbeterde error handling"""
        
        # Clean en valideer de URL
        cleaned_url, error = clean_url(url)
        if error:
            messagebox.showerror("URL Error", error)
            self.append_log(tab, f"URL Error: {error}")
            return
            
        try:
            # Update UI om te laten zien dat we bezig zijn
            tab.url_input.config(state="disabled")
            self.append_log(tab, f"Loading URL: {cleaned_url}")
            
            # Probeer de pagina te laden
            status = self.web_handler.load_page(cleaned_url)
            
            if status == "success":
                self.web_handler.take_screenshot()
                self.update_snapshot(tab)
                self.append_log(tab, f"Successfully loaded: {cleaned_url}")
            else:
                error_msg = f"Failed to load URL: {status}"
                messagebox.showerror("Loading Error", error_msg)
                self.append_log(tab, error_msg)
                
        except Exception as e:
            error_msg = f"Error accessing URL: {str(e)}"
            messagebox.showerror("Connection Error", error_msg)
            self.append_log(tab, error_msg)
            
        finally:
            # Altijd de URL input weer enablen
            tab.url_input.config(state="normal")

    # Verbeterde WebPageHandler load_page methode
    def load_page(self, url):
        """Laad een webpagina met verbeterde error handling"""
        try:
            self.driver.set_page_load_timeout(30)  # Maximum 30 seconden wachten
            self.driver.get(url)
            
            # Wacht tot de pagina echt geladen is
            start_time = time.time()
            while time.time() - start_time < 10:  # Maximum 10 seconden extra wachten
                state = self.driver.execute_script("return document.readyState")
                if state == "complete":
                    return "success"
                time.sleep(0.5)
                
            return "timeout: page did not fully load"
            
        except webdriver.common.exceptions.TimeoutException:
            return "timeout: page took too long to respond"
        except webdriver.common.exceptions.WebDriverException as e:
            if "net::ERR_NAME_NOT_RESOLVED" in str(e):
                return "domain not found"
            elif "net::ERR_CONNECTION_TIMED_OUT" in str(e):
                return "connection timed out"
            elif "net::ERR_CONNECTION_REFUSED" in str(e):
                return "connection refused by server"
            elif "net::ERR_CERT_" in str(e):
                return "SSL/security certificate error"
            else:
                return f"browser error: {str(e)}"
        except Exception as e:
            return f"unexpected error: {str(e)}"

    def get_snapshot(self):
        """Verkrijg een snapshot van de huidige pagina"""
        elements = self.driver.find_elements(By.XPATH, "//button | //input | //a")
        snapshot = {
            "url": self.driver.current_url,
            "title": self.driver.title,
            "html_preview": self.driver.page_source[:500],
            "elements": [
                {
                    "tag": element.tag_name,
                    "text": element.text,
                    "xpath": self.get_element_xpath(element),
                    "is_visible": element.is_displayed(),
                    "attributes": {
                        "id": element.get_attribute("id"),
                        "class": element.get_attribute("class"),
                        "name": element.get_attribute("name")
                    }
                } for element in elements
            ]
        }
        return json.dumps(snapshot)

    def perform_action(self, action):
        """Voer een actie uit op de pagina"""
        try:
            if action['type'] == 'CLICK':
                element = self.driver.find_element(By.XPATH, action['target'])
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)
                element.click()
            elif action['type'] == 'INPUT':
                element = self.driver.find_element(By.XPATH, action['target'])
                element.clear()
                element.send_keys(action['value'])
            elif action['type'] == 'SCROLL':
                element = self.driver.find_element(By.XPATH, action['target'])
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth'});", element)
            time.sleep(1)
            return "success"
        except Exception as e:
            return f"failure: {str(e)}"

    def take_screenshot(self, filename="snapshot.png"):
        """Maak een screenshot van de huidige pagina"""
        self.driver.save_screenshot(filename)

    @staticmethod
    def get_element_xpath(element):
        """Genereer een XPath voor een element"""
        components = []
        child = element
        while child:
            parent = child.find_element(By.XPATH, "..")
            siblings = parent.find_elements(By.XPATH, f"./{child.tag_name}")
            components.append(
                f"{child.tag_name}[{siblings.index(child) + 1}]" if len(siblings) > 1 else child.tag_name
            )
            child = parent if parent.tag_name != "html" else None
        components.reverse()
        return f"/{'/'.join(components)}"

class AgentExecutiveApp:
    """Hoofdapplicatie klasse"""
    def __init__(self, root):
        self.root = root
        self.root.title("AgentExecutive")
        self.root.geometry("1200x900")
        
        # Handlers initialiseren
        self.web_handler = WebPageHandler()
        self.llm_handler = LLMHandler(os.getenv("OPENAI_API_KEY"))
        
        # Main menu setup
        self.setup_menu()
        
        # Tabs setup
        self.tab_control = ttk.Notebook(root)
        self.add_new_tab()
        self.tab_control.pack(expand=1, fill="both")

    def setup_menu(self):
        """Setup het hoofdmenu"""
        self.main_menu = tk.Menu(self.root)
        self.root.config(menu=self.main_menu)
        
        file_menu = tk.Menu(self.main_menu, tearoff=0)
        file_menu.add_command(label="New", command=self.new_execution)
        file_menu.add_command(label="Save execution", command=self.save_execution)
        file_menu.add_command(label="Load execution", command=self.load_execution)
        file_menu.add_command(label="Logs", command=self.show_logs)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_application)
        self.main_menu.add_cascade(label="File", menu=file_menu)

    def add_new_tab(self):
        """Voeg een nieuwe tab toe"""
        new_tab = Frame(self.tab_control)
        tab_title = f"Assistant #{len(self.tab_control.tabs()) + 1}"
        self.tab_control.add(new_tab, text=tab_title)
        self.setup_tab_content(new_tab)

    def setup_tab_content(self, tab):
        """Setup de content van een tab"""
        # URL Input
        url_frame = Frame(tab)
        url_frame.pack(fill="x", padx=5, pady=5)
        
        url_label = tk.Label(url_frame, text="URL:")
        url_label.pack(side="left")
        
        url_input = tk.Entry(url_frame)
        url_input.pack(side="left", fill="x", expand=True, padx=5)
        
        go_button = tk.Button(url_frame, text="Go", 
                            command=lambda: self.load_url(url_input.get(), tab))
        go_button.pack(side="right")
        
        # Role & Goal
        input_frame = Frame(tab)
        input_frame.pack(fill="x", padx=5, pady=5)
        
        role_label = tk.Label(input_frame, text="Role:")
        role_label.grid(row=0, column=0, sticky="w")
        
        role_input = tk.Entry(input_frame)
        role_input.grid(row=0, column=1, sticky="ew", padx=5)
        
        goal_label = tk.Label(input_frame, text="Goal:")
        goal_label.grid(row=1, column=0, sticky="w")
        
        goal_input = tk.Entry(input_frame)
        goal_input.grid(row=1, column=1, sticky="ew", padx=5)
        
        # Execute Button
        execute_button = tk.Button(tab, text="Execute Step",
                                 command=lambda: self.execute_step(role_input.get(), 
                                                                 goal_input.get(), 
                                                                 tab))
        execute_button.pack(pady=10)
        
        # Snapshot Area
        snapshot_label = tk.Label(tab, text="Page Snapshot:")
        snapshot_label.pack(anchor="w", padx=5)
        
        snapshot_canvas = tk.Label(tab)
        snapshot_canvas.pack(pady=5)
        
        # Action & Output Areas
        action_frame = Frame(tab)
        action_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Next Action
        next_action_label = tk.Label(action_frame, text="Next Action:")
        next_action_label.pack(anchor="w")
        
        next_action_text = scrolledtext.ScrolledText(action_frame, height=3)
        next_action_text.pack(fill="x")
        
        # Previous Actions
        prev_actions_label = tk.Label(action_frame, text="Previous Actions:")
        prev_actions_label.pack(anchor="w")
        
        prev_actions_text = scrolledtext.ScrolledText(action_frame, height=10)
        prev_actions_text.pack(fill="both", expand=True)
        
        # Store references
        tab.url_input = url_input
        tab.role_input = role_input
        tab.goal_input = goal_input
        tab.snapshot_canvas = snapshot_canvas
        tab.next_action_text = next_action_text
        tab.prev_actions_text = prev_actions_text

    @threaded
    def load_url(self, url, tab):
        """Laad een URL en update de UI"""
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
            
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            
        status = self.web_handler.load_page(url)
        if status == "success":
            self.web_handler.take_screenshot()
            self.update_snapshot(tab)
            self.append_log(tab, f"Loaded URL: {url}")
        else:
            self.append_log(tab, f"Failed to load URL: {status}")

    @threaded
    def execute_step(self, role, goal, tab):
        """Voer een enkele stap uit"""
        if not role or not goal:
            messagebox.showerror("Error", "Please enter both role and goal")
            return
            
        snapshot = self.web_handler.get_snapshot()
        action = self.llm_handler.get_llm_action(snapshot, role, goal)
        
        if action.get('type') == 'ERROR':
            self.append_log(tab, f"Error getting action: {action['message']}")
            return
            
        self.update_next_action(tab, json.dumps(action, indent=2))
        
        status = self.web_handler.perform_action(action)
        if status == "success":
            self.append_previous_action(tab, action, "success")
            self.web_handler.take_screenshot()
            self.update_snapshot(tab)
        else:
            self.append_previous_action(tab, action, "failure")
            self.append_log(tab, f"Action failed: {status}")

    def update_snapshot(self, tab):
        """Update het snapshot in de UI"""
        try:
            image = Image.open("snapshot.png")
            image = image.resize((300, 200), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            tab.snapshot_canvas.config(image=photo)
            tab.snapshot_canvas.image = photo
        except Exception as e:
            self.append_log(tab, f"Error updating snapshot: {str(e)}")

    def update_next_action(self, tab, action_text):
        """Update het next action veld"""
        tab.next_action_text.delete('1.0', tk.END)
        tab.next_action_text.insert(tk.END, action_text)

    def append_previous_action(self, tab, action, status):
        """Voeg een actie toe aan de previous actions lijst"""
        tab.prev_actions_text.insert(tk.END, 
                                   f"[{status.upper()}] {json.dumps(action)}\n")
        tab.prev_actions_text.see(tk.END)

    def append_log(self, tab, message):
        """Voeg een bericht toe aan de log"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        tab.prev_actions_text.insert(tk.END, f"[{timestamp}] {message}\n")
        tab.prev_actions_text.see(tk.END)

    def new_execution(self):
        """Start een nieuwe executie"""
        self.add_new_tab()

    def save_execution(self):
        """Sla de huidige executie op"""
        filename = filedialog.asksaveasfilename(defaultextension=".json")
        if filename:
            current_tab = self.tab_control.select()
            tab = self.tab_control.nametowidget(current_tab)
            data = {
                "url": tab.url_input.get(),
                "role": tab.role_input.get(),
                "goal": tab.goal_input.get(),
                "actions": tab.prev_actions_text.get("1.0", tk.END)
            }
            with open(filename, 'w') as f:
                json.dump(data, f)

    def load_execution(self):
        """Laad een opgeslagen executie"""
        filename = filedialog.askopenfilename(defaultextension=".json")
        if filename:
            with open(filename, 'r') as f:
                data = json.load(f)
            self.add_new_tab()
            current_tab = self.tab_control.select()
            tab = self.tab_control.nametowidget(current_tab)
            tab.url_input.insert(0, data.get("url", ""))
            tab.role_input.insert(0, data.get("role", ""))
            tab.goal_input.insert(0, data.get("goal", ""))
            tab.prev_actions_text.insert("1.0", data.get("actions", ""))

    def show_logs(self):
        """Toon de logs in een apart venster"""
        log_window = tk.Toplevel(self.root)
        log_window.title("Execution Logs")
        log_window.geometry("600x400")
        
        log_text = scrolledtext.ScrolledText(log_window)
        log_text.pack(fill="both", expand=True)
        
        current_tab = self.tab_control.select()
        tab = self.tab_control.nametowidget(current_tab)
        log_text.insert("1.0", tab.prev_actions_text.get("1.0", tk.END))
        log_text.config(state="disabled")

    def exit_application(self):
        """Sluit de applicatie"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
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
    """Start de applicatie"""
    root = tk.Tk()
    app = AgentExecutiveApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()