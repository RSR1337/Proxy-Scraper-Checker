import requests
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk

FETCH_TIMEOUT = 10

proxy_sources = [
    'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
    'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt',
    'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
    'https://www.proxy-list.download/api/v1/get?type=http',
    'https://openproxy.space/list/http',
    'https://www.sslproxies.org',
    'https://www.us-proxy.org',
    'https://free-proxy-list.net',
    'https://www.socks-proxy.net',
    'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt',
    'https://www.proxynova.com/proxy-server-list/',
    'https://www.proxyhub.me/en/all-http-proxy-list.html',
    'https://raw.githubusercontent.com/opsxcq/proxy-list/master/list.txt',
    'https://www.ipaddress.com/proxy-list/',
    'https://hidemy.name/en/proxy-list/',
    'https://spys.one/en/https-ssl-proxy/',
    'https://www.proxylists.net/http_highanon.txt',
    'https://proxydb.net/?protocol=http',
    'https://www.geonode.com/free-proxy-list/',
    'https://proxy-list.org/english/index.php',
]

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36 OPR/62.0.3331.116',
]

test_urls = [
    'https://www.google.com',
    'https://www.github.com',
    'https://httpbin.org/ip',
]

def get_random_user_agent():
    return random.choice(user_agents)

def fetch_proxies_from_source(url, retries=3, backoff=2):
    attempt = 0
    while attempt < retries:
        try:
            headers = {'User-Agent': get_random_user_agent()}
            response = requests.get(url, headers=headers, timeout=FETCH_TIMEOUT)

            if response.status_code == 200:
                proxies = response.text.splitlines()
                proxies = [proxy.strip() for proxy in proxies if proxy.strip()]
                return proxies
        except requests.exceptions.Timeout:
            print(f"Fetching proxies from {url} timed out.")
            return []
        except Exception as e:
            print(f"Error fetching proxies from {url}: {e}")
            time.sleep(backoff)
            backoff *= 2
            attempt += 1
    return []

def check_proxy(proxy, timeout, retries):
    proxies = {
        'http': f'http://{proxy}',
        'https': f'http://{proxy}',
    }
    headers = {'User-Agent': get_random_user_agent()}

    for retry in range(retries):
        for url in test_urls:
            try:
                response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
                if response.status_code == 200 and response.text:
                    return proxy
            except Exception:
                pass
    return None

def scrape_and_check_proxies(output_area, button, progress_bar, progress_label, check_mode, disable_button):
    all_proxies = []
    
    button.config(state=tk.DISABLED)
    disable_button.config(state=tk.DISABLED)
    output_area.insert(tk.END, "Fetching proxies...\n")

    for source in proxy_sources:
        proxies = fetch_proxies_from_source(source)
        if proxies:
            all_proxies.extend(proxies)
            output_area.insert(tk.END, f"Fetched {len(proxies)} proxies from {source}\n")
        else:
            output_area.insert(tk.END, f"Failed to fetch proxies from {source}\n")
        output_area.update()

    if not all_proxies:
        output_area.insert(tk.END, "No proxies fetched. Please check the sources.\n")
        button.config(state=tk.NORMAL)
        disable_button.config(state=tk.NORMAL)
        return

    output_area.insert(tk.END, "Checking proxies...\n")
    output_area.update()

    total_proxies = len(all_proxies)
    working_proxies = []

    progress_bar["maximum"] = total_proxies
    progress_bar["value"] = 0

    if check_mode == "Quick Check":
        timeout = 3
        retries = 1
    else: 
        timeout = 10
        retries = 3

    with ThreadPoolExecutor(max_workers=150) as executor:
        futures = {executor.submit(check_proxy, proxy, timeout, retries): proxy for proxy in all_proxies}

        for idx, future in enumerate(as_completed(futures)):
            proxy = futures[future]
            result = future.result()
            if result:
                working_proxies.append(proxy)
                output_area.insert(tk.END, f"Working proxy found: {proxy}\n")
                output_area.update()

                with open('working_proxies.txt', 'a') as f:
                    f.write(proxy + '\n')

            progress_bar["value"] = idx + 1
            progress_label.config(text=f"Checking proxies... {idx + 1}/{total_proxies}")
            output_area.update()

    output_area.insert(tk.END, f"Found {len(working_proxies)} working proxies.\n")
    output_area.update()

    button.config(state=tk.NORMAL)
    disable_button.config(state=tk.NORMAL)

def start_scraping_thread(output_area, button, progress_bar, progress_label, check_mode, disable_button):
    threading.Thread(target=scrape_and_check_proxies, args=(output_area, button, progress_bar, progress_label, check_mode, disable_button), daemon=True).start()

def create_RSR_ui():
    global root
    root = tk.Tk()
    root.title("<RSR/> Proxy Scraper & Checker")
    
    root.resizable(False, False)

    frame = tk.Frame(root, padx=10, pady=10, bg="#1a1a1a") 
    frame.pack(fill=tk.BOTH, expand=True)

    quick_check_button = tk.Button(frame, text="Quick Check", fg="#39FF14", bg="#333", font=("Courier", 12, "bold"),
                                   activebackground="#222", activeforeground="#0FF",
                                   relief=tk.RAISED, bd=3,
                                   command=lambda: start_scraping_thread(output_area, quick_check_button, progress_bar, progress_label, "Quick Check", accurate_check_button))
    quick_check_button.pack(pady=10, side=tk.LEFT)

    accurate_check_button = tk.Button(frame, text="Accurate Check", fg="#39FF14", bg="#333", font=("Courier", 12, "bold"),
                                      activebackground="#222", activeforeground="#0FF",
                                      relief=tk.RAISED, bd=3,
                                      command=lambda: start_scraping_thread(output_area, accurate_check_button, progress_bar, progress_label, "Accurate Check", quick_check_button))
    accurate_check_button.pack(pady=10, side=tk.RIGHT)

    output_area = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=80, height=20, bg="#121212", fg="#39FF14",
                                            insertbackground="#39FF14", font=("Courier", 10), relief=tk.FLAT)
    output_area.pack(padx=10, pady=10)

    progress_bar = ttk.Progressbar(frame, orient="horizontal", length=400, mode="determinate", style="Custom.Horizontal.TProgressbar")
    progress_bar.pack(pady=5)
    
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Custom.Horizontal.TProgressbar", troughcolor="#333", background="#39FF14", thickness=20)

    progress_label = tk.Label(frame, text="Checking proxies... 0/0", fg="#39FF14", bg="#1a1a1a", font=("Courier", 12, "bold"))
    progress_label.pack()

    root.configure(bg="#1a1a1a")
    root.mainloop()

if __name__ == "__main__":
    create_RSR_ui()
