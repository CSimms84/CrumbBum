import argparse
import json
import os
import requests
import websocket
import time

class DebugData:
    def __init__(self, description="", devtoolsFrontendUrl="", id="", title="", type="", url="", webSocketDebuggerUrl="", faviconUrl="", **kwargs):
        self.description = description
        self.devtoolsFrontendUrl = devtoolsFrontendUrl
        self.faviconUrl = faviconUrl
        self.id = id
        self.title = title
        self.type = type
        self.url = url
        self.webSocketDebuggerUrl = webSocketDebuggerUrl
        for key, value in kwargs.items():
            setattr(self, key, value)

class LightCookie:
    def __init__(self, name, value, domain, path, expires):
        self.name = name
        self.value = value
        self.domain = domain
        self.path = path
        self.expires = expires

def get_debug_data(debug_port):
    debug_url = f"http://localhost:{debug_port}/json"
    response = requests.get(debug_url)
    print("Debug data fetched")
    debug_list = [DebugData(**item) for item in response.json()]
    print("Debug data parsed")
    return debug_list

def print_debug_data(debug_list, grep):
    grep_flag = bool(grep)
    for value in debug_list:
        if grep_flag:
            if grep in value.title or grep in value.url:
                print(f"Title: {value.title}\nType: {value.type}\nURL: {value.url}\nWebSocket Debugger URL: {value.webSocketDebuggerUrl}\n")
        else:
            print(f"Title: {value.title}\nType: {value.type}\nURL: {value.url}\nWebSocket Debugger URL: {value.webSocketDebuggerUrl}\n")

def dump_cookies(debug_list, format, grep):
    grep_flag = bool(grep)
    websocket_url = debug_list[0].webSocketDebuggerUrl
    print(f"Connecting to WebSocket: {websocket_url}")
    ws = websocket.create_connection(websocket_url, origin="http://localhost")
    print("WebSocket connected")
    message = json.dumps({"id": 1, "method": "Network.getAllCookies"})
    ws.send(message)
    print("Message sent to WebSocket")
    raw_response = ws.recv()
    print("Response received from WebSocket")
    print(f"Raw response: {raw_response[:1000]}...")  # Print only first 1000 characters for brevity
    websocket_response_root = json.loads(raw_response)
    
    if format == "raw":
        print(raw_response)
        os._exit(0)
    
    if format == "modified":
        light_cookie_list = []
        for value in websocket_response_root['result']['cookies']:
            if grep_flag:
                if grep in value['name'] or grep in value['domain']:
                    light_cookie = LightCookie(
                        name=value['name'],
                        value=value['value'],
                        domain=value['domain'],
                        path=value['path'],
                        expires=time.time() + 10 * 365 * 24 * 60 * 60
                    )
                    light_cookie_list.append(light_cookie)
            else:
                light_cookie = LightCookie(
                    name=value['name'],
                    value=value['value'],
                    domain=value['domain'],
                    path=value['path'],
                    expires=time.time() + 10 * 365 * 24 * 60 * 60
                )
                light_cookie_list.append(light_cookie)
        
        light_cookie_json = json.dumps([light_cookie.__dict__ for light_cookie in light_cookie_list])
        print(light_cookie_json)
        os._exit(0)
    
    print(f"Number of cookies: {len(websocket_response_root['result']['cookies'])}")
    for value in websocket_response_root['result']['cookies']:
        if grep_flag:
            if grep in value['name'] or grep in value['domain']:
                print(f"name: {value['name']}\nvalue: {value['value']}\ndomain: {value['domain']}\npath: {value['path']}\nexpires: {value['expires']}\nsize: {value['size']}\nhttpOnly: {value['httpOnly']}\nsecure: {value['secure']}\nsession: {value['session']}\nsameSite: {value.get('sameSite', 'N/A')}\npriority: {value['priority']}\n")
        else:
            print(f"name: {value['name']}\nvalue: {value['value']}\ndomain: {value['domain']}\npath: {value['path']}\nexpires: {value['expires']}\nsize: {value['size']}\nhttpOnly: {value['httpOnly']}\nsecure: {value['secure']}\nsession: {value['session']}\nsameSite: {value.get('sameSite', 'N/A')}\npriority: {value['priority']}\n")

def clear_cookies(debug_list):
    websocket_url = debug_list[0].webSocketDebuggerUrl
    ws = websocket.create_connection(websocket_url, origin="http://localhost")
    message = json.dumps({"id": 1, "method": "Network.clearBrowserCookies"})
    ws.send(message)

def load_cookies(debug_list, load):
    with open(load, 'r') as file:
        content = file.read()
    websocket_url = debug_list[0].webSocketDebuggerUrl
    ws = websocket.create_connection(websocket_url, origin="http://localhost")
    message = json.dumps({"id": 1, "method": "Network.setCookies", "params": {"cookies": json.loads(content)}})
    ws.send(message)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Interact with Chromium-based browsers' debug port to view open tabs, installed extensions, and cookies")
    parser.add_argument("-p", "--port", required=True, help="{REQUIRED} - Debug port")
    parser.add_argument("-d", "--dump", required=False, help="{ pages || cookies } - Dump open tabs/extensions or cookies")
    parser.add_argument("-f", "--format", required=False, help="{ raw || human || modified } - Format when dumping cookies")
    parser.add_argument("-g", "--grep", required=False, help="Narrow scope of dumping to specific name/domain")
    parser.add_argument("-l", "--load", required=False, help="File name for cookies to load into browser")
    parser.add_argument("-c", "--clear", required=False, help="Clear cookies before loading new cookies")
    args = parser.parse_args()

    if args.dump:
        debug_list = get_debug_data(args.port)
        if args.dump == "pages":
            print_debug_data(debug_list, args.grep)
        elif args.dump == "cookies":
            dump_cookies(debug_list, args.format, args.grep)

    if args.clear:
        debug_list = get_debug_data(args.port)
        clear_cookies(debug_list)

    if args.load:
        debug_list = get_debug_data(args.port)
        load_cookies(debug_list, args.load)
