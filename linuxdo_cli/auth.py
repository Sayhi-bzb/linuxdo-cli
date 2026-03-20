import webbrowser
import httpx
import secrets
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
from typing import Optional
from .config import Config, save_config
from rich import print

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """处理 Linux Do Connect OAuth2 回调"""
    def do_GET(self):
        query = urlparse(self.path).query
        params = parse_qs(query)
        if "code" in params:
            self.server.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h1>授权成功！</h1><p>授权码已成功传输到 CLI，请返回终端。</p><script>setTimeout(window.close, 3000);</script>".encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write("<h1>授权失败</h1><p>未能在回调中找到授权码。</p>".encode("utf-8"))

    def log_message(self, format, *args):
        # 禁用日志输出到终端，保持界面整洁
        return

def login(config: Config) -> Optional[Config]:
    """
    使用 Linux Do Connect OAuth2 流程登录：
    1. 引导用户访问授权页面
    2. 启动本地服务器接收 code
    3. 换取 Access Token
    4. 获取用户信息及 API Key
    """
    state = secrets.token_hex(16)
    redirect_uri = "http://localhost:8080"
    
    params = {
        "client_id": config.client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "user",
        "state": state
    }
    
    auth_url = f"{config.connect_url}/oauth2/authorize?{urlencode(params)}"

    print(f"\n[bold cyan]正在启动 OAuth2 授权流程...[/bold cyan]")
    print(f"请在浏览器中完成授权。如果浏览器未自动打开，请手动访问：\n[link={auth_url}]{auth_url}[/link]\n")
    
    # 启动本地服务器
    server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
    server.auth_code = None
    
    webbrowser.open(auth_url)

    # 等待回调
    try:
        server.handle_request()
    except KeyboardInterrupt:
        print("\n[red]已取消登录。[/red]")
        return None

    code = server.auth_code
    if not code:
        print("[red]未能获取授权码。[/red]")
        return None

    print("[green]已获取授权码，正在换取 Access Token...[/green]")

    # 换取 Access Token
    try:
        with httpx.Client() as client:
            token_res = client.post(
                f"{config.connect_url}/oauth2/token",
                data={
                    "client_id": config.client_id,
                    "client_secret": config.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                }
            )
            token_res.raise_for_status()
            token_data = token_res.json()
            
            config.access_token = token_data.get("access_token")
            config.refresh_token = token_data.get("refresh_token")

            print("[green]成功获取 Access Token，正在拉取用户信息...[/green]")

            # 获取用户信息
            user_res = client.get(
                f"{config.connect_url}/api/user",
                headers={"Authorization": f"Bearer {config.access_token}"}
            )
            user_res.raise_for_status()
            user_data = user_res.json()
            username = user_data.get("username", "")

            save_config(config)
            print(f"\n[bold green]登录成功！[/bold green]")
            print(f"欢迎回来, [bold yellow]{username}[/bold yellow]!")
            
            return config
            
    except Exception as e:
        print(f"\n[red]登录过程中发生错误:[/red] {e}")
        return None
