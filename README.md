# ZERO-Sijuly

ZERO-Sijuly 是一个用于 Cloudflare Zero Trust / WARP Teams 的本地配置生成脚本。

脚本会通过 Cloudflare Access 邮箱验证码登录，自动注册 WARP 设备，并输出多个客户端可用的 WireGuard 配置。

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
bash <(curl -fsSL https://raw.githubusercontent.com/SIJULY/ZERO-Sijuly/main/ZERO-Sijuly.py)
```

备用命令：

```bash
curl -fsSL https://raw.githubusercontent.com/SIJULY/ZERO-Sijuly/main/ZERO-Sijuly.py -o ZERO-Sijuly.py && python3 ZERO-Sijuly.py
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

运行脚本后，按提示输入：

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

## 输出内容

脚本成功运行后，会输出以下几类配置：

- Surge：`[Proxy]` 节点行和 `[WireGuard ZERO]` 配置段。
- Stash / Mihomo / Clash Meta：可放入 `proxies:` 下的 WireGuard YAML 节点。
- Loon：可放入 `[Proxy]` 段的一行 WireGuard 节点。
- Shadowrocket / 小火箭：`[Proxy]` 节点行和 `[WireGuard ZERO]` 配置段。

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
