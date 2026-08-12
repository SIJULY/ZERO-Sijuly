#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import base64
import urllib.request
import ssl
import datetime
import re
import secrets
import subprocess
import platform
import importlib.util
import importlib


# ==========================================
# 0. 跨平台依赖检测 / 自动安装
# ==========================================
def run_cmd(cmd, check=False):
    """执行命令并返回是否成功。"""
    try:
        result = subprocess.run(cmd, check=check)
        return result.returncode == 0
    except Exception:
        return False


def install_python_package(package):
    print(f"📦 正在安装 Python 依赖：{package} ...")
    commands = [
        [sys.executable, "-m", "pip", "install", "--upgrade", package],
        [sys.executable, "-m", "pip", "install", "--user", "--upgrade", package],
    ]
    for cmd in commands:
        if run_cmd(cmd):
            return True
    return False


def ensure_playwright_package():
    if importlib.util.find_spec("playwright") is not None:
        return True

    print("⚠️ 未检测到 playwright，准备自动安装。")
    if install_python_package("playwright"):
        importlib.invalidate_caches()
        return True

    print("❌ playwright 自动安装失败。请手动执行：")
    print(f"   {sys.executable} -m pip install playwright")
    return False


def ensure_playwright_browser(sync_playwright_func):
    """检测 Chromium 是否可启动；不可启动则自动安装 Playwright Chromium。"""
    try:
        with sync_playwright_func() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True
    except Exception as e:
        msg = str(e)
        if "Executable doesn't exist" not in msg and "playwright install" not in msg and "Host system is missing dependencies" not in msg:
            # 不是浏览器缺失/系统依赖缺失，也继续尝试安装一次，避免误判。
            print(f"⚠️ Chromium 启动检测异常，将尝试修复：{e}")
        else:
            print("⚠️ 未检测到可用的 Playwright Chromium，准备自动安装。")

    if not run_cmd([sys.executable, "-m", "playwright", "install", "chromium"]):
        print("❌ Chromium 自动安装失败。请手动执行：")
        print(f"   {sys.executable} -m playwright install chromium")
        return False

    if platform.system().lower() == "linux":
        # Linux VPS 上 Chromium 可能还需要系统库。root 环境可自动装；非 root 失败后给出提示。
        print("🔧 当前是 Linux，正在检测/尝试安装 Chromium 系统依赖...")
        if not run_cmd([sys.executable, "-m", "playwright", "install-deps", "chromium"]):
            print("⚠️ 系统依赖自动安装失败或权限不足。")
            print("   如果后续 Chromium 启动失败，请在 VPS 上手动执行：")
            print(f"   sudo {sys.executable} -m playwright install-deps chromium")

    try:
        with sync_playwright_func() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True
    except Exception as e:
        print(f"❌ Chromium 仍然无法启动：{e}")
        print("请按上方提示补齐系统依赖后重新运行脚本。")
        return False


def ensure_runtime_dependencies():
    """确保脚本运行所需依赖可用。"""
    print("🔍 正在检查运行环境...")
    print(f"   系统：{platform.system()} {platform.release()}")
    print(f"   Python：{sys.version.split()[0]}")

    if sys.version_info < (3, 8):
        print("❌ Python 版本过低，请使用 Python 3.8 或更高版本。")
        sys.exit(1)

    if not ensure_playwright_package():
        sys.exit(1)

    try:
        from playwright.sync_api import sync_playwright as _sync_playwright
    except Exception as e:
        print(f"❌ playwright 导入失败：{e}")
        sys.exit(1)

    if not ensure_playwright_browser(_sync_playwright):
        sys.exit(1)

    print("✅ 运行环境检查完成。\n")
    return _sync_playwright


sync_playwright = None

# ==========================================
# 1. X25519 密钥生成算法 (纯 Python)
# ==========================================
_P = 2 ** 255 - 19
_A24 = 121665


def _decode_scalar(k): k = bytearray(k); k[0] &= 248; k[31] &= 127; k[31] |= 64; return int.from_bytes(k, "little")


def _decode_u(u): u = bytearray(u); u[31] &= 127; return int.from_bytes(u, "little")


def _x25519(s, p):
    k = _decode_scalar(s);
    x1 = _decode_u(p);
    x2, z2 = 1, 0;
    x3, z3 = x1, 1;
    swap = 0
    for t in range(254, -1, -1):
        kt = (k >> t) & 1;
        swap ^= kt
        if swap: x2, x3 = x3, x2; z2, z3 = z3, z2
        swap = kt
        A = (x2 + z2) % _P;
        AA = (A * A) % _P;
        B = (x2 - z2) % _P;
        BB = (B * B) % _P
        E = (AA - BB) % _P;
        C = (x3 + z3) % _P;
        D = (x3 - z3) % _P
        DA = (D * A) % _P;
        CB = (C * B) % _P
        x3 = ((DA + CB) % _P) ** 2 % _P;
        z3 = (x1 * (((DA - CB) % _P) ** 2)) % _P
        x2 = (AA * BB) % _P;
        z2 = (E * ((AA + (_A24 * E) % _P) % _P)) % _P
    if swap: x2, x3 = x3, x2; z2, z3 = z3, z2
    return ((x2 * pow(z2, _P - 2, _P)) % _P).to_bytes(32, "little")


def generate_keypair():
    priv = bytearray(os.urandom(32));
    priv[0] &= 248;
    priv[31] &= 127;
    priv[31] |= 64
    pub = _x25519(bytes(priv), bytes([9] + [0] * 31))
    return base64.b64encode(priv).decode(), base64.b64encode(pub).decode()


# ==========================================
# 2. 网络请求通用工具 (Cloudflare API)
# ==========================================
def http_request(method, url, headers, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ssl._create_unverified_context()) as r:
            return r.read().decode('utf-8')
    except Exception as e:
        print(f"❌ 网络请求失败: {e}")
        sys.exit(1)


# ==========================================
# 3. Playwright 隐形模式提取 WARP 注册 Token
# ==========================================
def get_cf_token_via_playwright(org, email):
    warp_auth_url = None
    access_jwt = None
    cf_authorization = None

    def extract_from_text(text):
        if not text:
            return None, None

        url_match = re.search(r"com\.cloudflare\.warp://[^\s\"'<>]+", text)
        if url_match:
            url = url_match.group(0)
            jwt_match = re.search(r"[?&]token=([^&\s\"'<>]+)", url)
            return url, jwt_match.group(1) if jwt_match else None

        jwt_match = re.search(r"token=([A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)", text)
        if jwt_match:
            return None, jwt_match.group(1)

        return None, None

    with sync_playwright() as p:
        # headless=True：全程在后台静默运行，不会弹出任何浏览器窗口！
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        def capture_token_from_url(url):
            nonlocal warp_auth_url, access_jwt
            found_url, found_jwt = extract_from_text(url)
            if found_url:
                warp_auth_url = found_url
            if found_jwt:
                access_jwt = found_jwt

        page.on("request", lambda req: capture_token_from_url(req.url))
        page.on("response", lambda resp: capture_token_from_url(resp.url))

        login_url = f"https://{org}.cloudflareaccess.com/warp"
        print(f"🌍 [后台] 正在初始化安全会话并获取 Cookie...")
        page.goto(login_url)

        # 1. 自动填邮箱 (精准匹配你截图里的元素)
        print(f"⏳ [后台] 正在提交授权邮箱...")
        email_input = page.get_by_placeholder("example@email.com")
        email_input.wait_for(state="visible", timeout=15000)
        email_input.fill(email)

        page.get_by_role("button", name="Send login code").click()

        # 2. 等待你的输入
        otp = input("\n>>> ✅ 验证码已发送！请查收邮件并输入 6 位验证码: ").strip()
        print("⏳ [后台] 正在提交验证码并拦截底层 Token...")

        # 3. 自动填验证码 (兼容多种元素命名规则)
        try:
            # 大多数情况下，输入框的 name 是 code
            code_input = page.locator('input[name="code"]')
            code_input.wait_for(state="visible", timeout=10000)
            code_input.fill(otp)
        except:
            # 如果找不到，直接抓取页面上的第一个输入框
            page.locator('input').first.fill(otp)

        page.locator('button[type="submit"]').click()

        # 等待页面跳转，并尽量提取教程网页同款 com.cloudflare.warp://.../auth?token=JWT
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except:
            pass

        capture_token_from_url(page.url)

        # 有些页面会把 token 放在 textarea / input / 页面文本中。
        for selector in ["textarea", "input", "body"]:
            try:
                elements = page.locator(selector)
                count = min(elements.count(), 8)
                for i in range(count):
                    el = elements.nth(i)
                    text = ""
                    try:
                        text = el.input_value(timeout=1000)
                    except:
                        try:
                            text = el.inner_text(timeout=1000)
                        except:
                            pass
                    found_url, found_jwt = extract_from_text(text)
                    if found_url:
                        warp_auth_url = found_url
                    if found_jwt:
                        access_jwt = found_jwt
            except:
                pass

        cookies = context.cookies()
        for c in cookies:
            if c['name'] == 'CF_Authorization':
                cf_authorization = c['value']
                if not access_jwt:
                    access_jwt = c['value']
                break

        browser.close()

    if not access_jwt:
        print("❌ 未能截获 Token。可能是验证码错误，或者你的 IP 被隐形盾拦截了。")
        sys.exit(1)

    if warp_auth_url:
        print("✅ 成功在后台截获 WARP 注册 Token！\n")
    elif cf_authorization:
        print("⚠️ 仅截获到 CF_Authorization，未看到 com.cloudflare.warp:// 链接，将按 Access JWT 继续尝试。\n")
    else:
        print("✅ 成功在后台截获 Access JWT！\n")

    return {
        "warp_auth_url": warp_auth_url,
        "access_jwt": access_jwt,
        "cf_authorization": cf_authorization,
    }


def random_install_id():
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(22))


def client_id_to_reserved(client_id):
    """把 Surge client-id 格式转换为 Stash/Mihomo WireGuard reserved 数组。"""
    if not client_id:
        return None

    parts = client_id.split("/")
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        nums = [int(p) for p in parts]
        if all(0 <= n <= 255 for n in nums):
            return nums

    return None


# ==========================================
# 4. 核心执行流程
# ==========================================
def main():
    print("=" * 60)
    print(" 🚀 CF Zero Trust 本地后台静默全自动版")
    print("=" * 60 + "\n")

    org = input(">>> 请输入 Organization (Team Name): ").strip()
    email = input(">>> 请输入 Email (授权邮箱): ").strip()
    proxy_name = input(">>> 请输入 Surge 节点名称 [默认 WARP]: ").strip() or "WARP"

    # 1. 后台无缝获取 WARP 注册 Token
    token_info = get_cf_token_via_playwright(org, email)
    access_jwt = token_info["access_jwt"]

    # 2. 生成密钥并注册设备
    print("⏳ 正在生成本地密钥并向 Cloudflare 注册设备...")
    priv_key, pub_key = generate_keypair()

    CF_API = "https://api.cloudflareclient.com/v0a2158"
    CF_HEADERS = {
        "User-Agent": "okhttp/3.12.1",
        "CF-Client-Version": "a-6.10-2158",
        "Content-Type": "application/json"
    }

    install_id = random_install_id()
    fcm_token = f"{install_id}:APA91b{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(134))}"

    reg_body = {
        "key": pub_key, "install_id": install_id, "fcm_token": fcm_token,
        "tos": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "model": "PC", "serial_number": install_id, "locale": "zh_CN"
    }

    # 关键修正：fscarmen/api.sh 是在注册设备时直接带 Cf-Access-Jwt-Assertion，
    # 而不是先注册普通 WARP 再 PUT /account。这样生成的 Teams 设备更接近教程里的可用节点。
    reg_headers = dict(CF_HEADERS)
    reg_headers["Cf-Access-Jwt-Assertion"] = access_jwt
    reg_resp = json.loads(http_request("POST", f"{CF_API}/reg", reg_headers, reg_body))
    device_id = reg_resp.get("id")
    device_token = reg_resp.get("token")

    auth_headers = dict(CF_HEADERS)
    auth_headers["Authorization"] = f"Bearer {device_token}"

    print("⏳ 正在拉取 Cloudflare 最终路由配置...")
    conf_resp = json.loads(http_request("GET", f"{CF_API}/reg/{device_id}", auth_headers))
    conf_resp["private_key"] = priv_key

    debug_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "warp-account-debug.json")
    with open(debug_path, "w", encoding="utf-8") as f:
        json.dump(conf_resp, f, ensure_ascii=False, indent=2)

    config = conf_resp["config"]

    client_id = config.get("client_id", "")
    addresses = config["interface"]["addresses"]
    self_ipv4 = addresses["v4"]
    self_ipv6 = addresses.get("v6") or "2606:4700:cf1:1000::2"
    peer_pub = config["peers"][0]["public_key"]
    reserved = client_id_to_reserved(client_id)

    # 3. 输出 Surge 纯净版配置
    proxy_line = f"{proxy_name} = wireguard, section-name=ZERO"

    peer_line = (
        f"peer = (public-key = {peer_pub}, allowed-ips = 0.0.0.0/0, "
        f"endpoint = 162.159.193.10:2408, keepalive = 45"
    )
    if client_id:
        peer_line += f", client-id = {client_id})"
    else:
        peer_line += ")"

    print("\n" + "=" * 18 + " 🎉 您的专属 Surge 配置 🎉 " + "=" * 18 + "\n")
    print("① 把下面这行放进 [Proxy] 段")
    print(proxy_line)
    print("\n② 把下面整段放进配置文件（可放独立分区）")
    print("[WireGuard ZERO]")
    print(f"private-key = {priv_key}")
    print(f"self-ip = {self_ipv4}")
    print("dns-server = 1.1.1.1")
    print("mtu = 1280")
    print(peer_line)

    print("\n" + "=" * 18 + " 🎉 您的专属Stash 配置 🎉 " + "=" * 18 + "\n")
    print("Stash / Mihomo / Clash Meta 可参考下面这段放进 proxies:\n")
    print(f"  - name: {proxy_name}")
    print("    type: wireguard")
    print("    server: 162.159.193.10")
    print("    port: 2408")
    print(f"    ip: {self_ipv4}")
    print(f"    ipv6: {self_ipv6}")
    print(f"    private-key: {priv_key}")
    print(f"    public-key: {peer_pub}")
    if reserved:
        print(f"    reserved: [{reserved[0]}, {reserved[1]}, {reserved[2]}]")
    print("    dns: [1.1.1.1]")
    print("    mtu: 1280")
    print("    udp: true")
    print("    benchmark-url: http://cp.cloudflare.com/generate_204")

    print("\n" + "=" * 18 + " 🎉 您的专属 LOON 配置 🎉 " + "=" * 18 + "\n")
    print("下面这段放进 [Proxy] 段:\n")
    loon_line = (
        f"{proxy_name} = wireguard, server=162.159.193.10, port=2408, "
        f"ip={self_ipv4}, ipv6={self_ipv6}, private-key={priv_key}, "
        f"public-key={peer_pub}, dns=1.1.1.1, mtu=1280, keepalive=45, udp=true"
    )
    if reserved:
        loon_line += f", reserved={reserved[0]}/{reserved[1]}/{reserved[2]}"
    print(loon_line)

    print("\n" + "=" * 12 + " 🎉 您的专属Shadowrocket / 小火箭 配置 🎉" + "=" * 12 + "\n")
    print("# 把下面这行放进 [Proxy] 段")
    shadowrocket_proxy_line = f"{proxy_name} = wireguard, section-name=ZERO"
    print(shadowrocket_proxy_line)
    print("\n# 把下面整段放进配置文件，可放在 [MITM] 前后独立分区")
    print("[WireGuard ZERO]")
    print(f"private-key = {priv_key}")
    print(f"self-ip = {self_ipv4}")
    print(f"self-ip-v6 = {self_ipv6}")
    print("dns-server = 1.1.1.1")
    print("mtu = 1280")
    print(peer_line)

    print(f"\n🧾 已保存注册返回 JSON：{debug_path}")
    print("\n" + "=" * 62)


if __name__ == "__main__":
    try:
        sync_playwright = ensure_runtime_dependencies()
        main()
    except KeyboardInterrupt:
        print("\n已取消。")
