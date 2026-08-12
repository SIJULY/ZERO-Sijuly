# ZERO-Sijuly

ZERO-Sijuly 是一个用于 Cloudflare Zero Trust / WARP Teams 的本地工具脚本。

脚本运行后可以选择：

- 提取 Cloudflare Zero Trust / WARP Teams 节点信息。
- 扫描并优选 Cloudflare WARP Endpoint IP。

节点提取功能会通过 Cloudflare Access 邮箱验证码登录，自动注册 WARP 设备，并输出多个客户端可用的 WireGuard 配置。

支持输出：

- Surge
- Stash / Mihomo / Clash Meta
- Loon
- Shadowrocket / 小火箭

> 本项目仅用于个人学习、测试和自用配置生成。请遵守 Cloudflare 服务条款以及你所在地的法律法规。

---

## 功能特点

- 使用 Python 运行。
- 自动检查 Python 版本。
- 自动检测并安装 Playwright。
- 自动安装 Playwright Chromium 浏览器。
- 后台静默登录 Cloudflare Access，不弹出浏览器窗口。
- 自动生成 WireGuard X25519 密钥。
- 自动注册 Cloudflare WARP Teams 设备。
- 自动输出 Surge、Stash、Loon、小火箭等配置。
- 自动保存 Cloudflare 注册返回 JSON 到 `warp-account-debug.json`，方便排查问题。
- 内置 Cloudflare WARP IP 优选扫描器。
- 通过 TCP Ping 测试 WARP Endpoint 连通性和延迟。
- 自动输出延迟最低的前 10 个可用 Endpoint。

---

## 环境要求

- Python 3.8 或更高版本。
- macOS、Linux、Windows 均可尝试运行。
- 已拥有 Cloudflare Zero Trust Team Name。
- 授权邮箱可以收到 Cloudflare Access 验证码。

查看 Python 版本：

```bash
python3 --version
```

---

## 一键运行

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/SIJULY/ZERO-Sijuly/main/ZERO-Sijuly.py -o ZERO-Sijuly.py && python3 ZERO-Sijuly.py
```

备用命令：

```bash
python3 <(curl -fsSL https://raw.githubusercontent.com/SIJULY/ZERO-Sijuly/main/ZERO-Sijuly.py)
```

### macOS Homebrew Python

```bash
curl -fsSL https://raw.githubusercontent.com/SIJULY/ZERO-Sijuly/main/ZERO-Sijuly.py -o ZERO-Sijuly.py && /opt/homebrew/bin/python3 ZERO-Sijuly.py
```

### Windows PowerShell

```powershell
iwr -useb https://raw.githubusercontent.com/SIJULY/ZERO-Sijuly/main/ZERO-Sijuly.py -OutFile ZERO-Sijuly.py
python ZERO-Sijuly.py
```

---

## 手动下载运行

```bash
git clone https://github.com/SIJULY/ZERO-Sijuly.git
cd ZERO-Sijuly
python3 ZERO-Sijuly.py
```

---

## 使用方法

运行脚本后，会先显示功能菜单：

```text
============================================================
 🚀 ZERO-Sijuly 工具箱
============================================================
1. 提取 Cloudflare Zero Trust / WARP 节点信息
2. Cloudflare WARP IP 优选
0. 退出
============================================================
>>> 请选择功能 [1/2/0]:
```

---

### 1. 提取 WARP 节点信息

选择 `1` 后，按提示输入：

```text
>>> 请输入 Organization (Team Name):
>>> 请输入 Email (授权邮箱):
>>> 请输入 Surge 节点名称 [默认 WARP]:
```

说明：

- `Organization (Team Name)` 是你的 Cloudflare Zero Trust 团队短名称。
  - 例如访问地址是 `https://sjune.cloudflareaccess.com`，那么 Team Name 就是 `sjune`。
- `Email` 必须是该 Zero Trust 组织授权策略允许登录的邮箱。
- `Surge 节点名称` 可以直接回车，默认使用 `WARP`。

输入邮箱后，Cloudflare 会发送 6 位验证码。收到验证码后输入即可继续。

---

### 2. Cloudflare WARP IP 优选

选择 `2` 后，脚本会从内置的 Cloudflare WARP IPv4 地址段中随机抽取 IP，并通过 TCP 连接测试 `2408` 端口延迟。

默认测试参数：

```text
测试端口：2408
超时时间：1.0 秒
随机抽样：100 个 IP
并发线程：50
```

扫描完成后会输出延迟最低的前 10 个 Endpoint，例如：

```text
[1] 延迟:  12.0 ms  =>  endpoint = 188.114.97.170:2408
[2] 延迟:  12.2 ms  =>  endpoint = 162.159.192.2:2408
```

你可以把优选出来的 Endpoint 替换到 Surge、Loon、小火箭等 WireGuard 配置中的 endpoint/server 字段。

---

## 输出内容

选择节点提取功能并成功运行后，会输出以下几类配置：

- Surge：`[Proxy]` 节点行和 `[WireGuard ZERO]` 配置段。
- Stash / Mihomo / Clash Meta：可放入 `proxies:` 下的 WireGuard YAML 节点。
- Loon：可放入 `[Proxy]` 段的一行 WireGuard 节点。
- Shadowrocket / 小火箭：`[Proxy]` 节点行和 `[WireGuard ZERO]` 配置段。

选择 IP 优选功能并成功运行后，会输出：

- 可用 WARP Endpoint 列表。
- 每个 Endpoint 的 TCP 握手延迟。
- 默认显示延迟最低的前 10 个结果。

---

## 常见问题

### 1. Team Name 是什么？

Team Name 是 Cloudflare Zero Trust 的组织短名称。

如果你的 Access 地址是：

```text
https://example.cloudflareaccess.com
```

那么 Team Name 就是：

```text
example
```

### 2. 收不到验证码怎么办？

请检查：

- Team Name 是否输入正确。
- 邮箱是否已被加入 Cloudflare Zero Trust 授权策略。
- 邮箱垃圾箱是否有验证码邮件。
- 当前网络是否可以访问 Cloudflare Access。

### 3. Playwright 安装失败怎么办？

可以手动执行：

```bash
python3 -m pip install --upgrade playwright
python3 -m playwright install chromium
```

Linux 服务器如果缺少 Chromium 系统依赖，可以尝试：

```bash
sudo python3 -m playwright install-deps chromium
```

### 4. `warp-account-debug.json` 是什么？

这是 Cloudflare 注册设备后返回的原始 JSON 文件，方便排查问题。其中可能包含设备信息，请不要公开分享。

### 5. 提示未能截获 Token 怎么办？

可能原因：

- 验证码输入错误。
- 邮箱没有通过 Access 授权策略。
- Team Name 填写错误。
- 当前 IP 被 Cloudflare Access 风控或防火墙拦截。
- Cloudflare 修改了登录页面结构。

可以换网络、确认授权邮箱、重新运行脚本后再试。

### 6. IP 优选没有结果怎么办？

可能原因：

- 当前网络无法连接 Cloudflare WARP 的 `2408` 端口。
- 本地防火墙、运营商或网络策略阻断了相关 IP 段。
- 默认超时时间 `1.0` 秒过短。
- 随机抽样的 IP 在当前网络下不可用。

可以稍后重新扫描，或根据需要修改脚本中的：

```python
TIMEOUT = 1.0
SAMPLE_SIZE = 100
MAX_WORKERS = 50
```

---

## 安全提醒

请不要公开分享以下内容：

- WireGuard private-key。
- Cloudflare Access Token。
- `warp-account-debug.json`。
- 任何包含账号或设备注册信息的日志。

---

## License

MIT License
