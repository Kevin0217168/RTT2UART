# RTT2UART

将 J-Link RTT（Real-Time Transfer）通道桥接为虚拟串口，让你可以用任意串口工具（minicom、screen、Putty、SSCOM 等）与目标 MCU 进行 RTT 通信。

## 工作原理

MCU 内部有一个 RTT 环形缓冲区，J-Link 通过 SWD/JTAG 直接读写 MCU RAM 即可完成数据收发。RTT2UART 将这个内存通信通道映射到一个虚拟串口上，使传统串口工具也能使用 RTT。

<pre>
MCU RTT 缓冲区 &lt;—SWD—&gt; J-Link 调试器 &lt;—USB—&gt; RTT Telnet Server(localhost:19021) &lt;—TCP—&gt; RTT2UART &lt;—&gt; 虚拟串口对 &lt;—&gt; 串口终端工具
</pre>

**为什么不直接使用物理串口？** RTT 不占用 MCU 的 UART 外设和引脚，速度更快（可达 MB/s），且不需要额外的电平转换硬件。

## 环境要求

- Python 3.8+
- J-Link 调试器 + 驱动（[SEGGER J-Link Software](https://www.segger.com/downloads/jlink/)）
  - 已验证版本：**V9.60**（2026-07-15）
  - 更早或更新版本通常也能正常工作
- 目标 MCU 固件已启用 SEGGER RTT
- **Linux**：`socat`（虚拟串口）
- **Windows**：[com0com](http://com0com.sourceforge.net/)（虚拟串口）

---

## 安装

### 1. 克隆项目并安装 Python 依赖

```bash
cd RTT2UART
pip install -r requirements.txt
```

### 2. Linux：安装虚拟串口对

**推荐：使用 `tty0tty` 内核模块**（注册到内核串口子系统，VOFA+、Putty 等均能自动发现）

```bash
# 安装依赖
sudo apt install git build-essential linux-headers-$(uname -r)

# 克隆并编译
git clone https://github.com/freemed/tty0tty.git /tmp/tty0tty
cd /tmp/tty0tty/module
make

# 安装模块
sudo cp tty0tty.ko /lib/modules/$(uname -r)/kernel/drivers/tty/
sudo depmod

# 安装 udev 规则（设置 dialout 组权限）
sudo cp 50-tty0tty.rules /etc/udev/rules.d/

# 加载模块
sudo modprobe tty0tty
sudo udevadm trigger

# 开机自动加载
echo 'tty0tty' | sudo tee -a /etc/modules
```

加载后产生 4 对虚拟串口：

| 对 1 | 对 2 | 对 3 | 对 4 |
|------|------|------|------|
| `/dev/tnt0` ↔ `/dev/tnt1` | `/dev/tnt2` ↔ `/dev/tnt3` | `/dev/tnt4` ↔ `/dev/tnt5` | `/dev/tnt6` ↔ `/dev/tnt7` |

> **备选：socat**（虚拟终端，但 VOFA 等工具无法自动发现）
>
> ```bash
> socat -d -d pty,raw,echo=0,link=/tmp/ttyV0 pty,raw,echo=0,link=/tmp/ttyV1
> ```
>
> RTT2UART 的 Scan 按钮会自动扫描上述所有设备类型（`/dev/tnt*`、`/dev/ttyS*`、`/tmp/ttyV*`）。

### 3. Windows：安装 com0com 并创建虚拟串口对

下载并安装 [com0com](http://com0com.sourceforge.net/)，添加一对虚拟串口（如 COM4 ↔ COM5）。

### 4. 验证 J-Link 驱动

```bash
# 确认 J-Link 驱动已正确安装
JLinkExe -?

# 查看版本输出，例如：
# SEGGER J-Link Commander V9.60 (Compiled Jul 15 2026 14:46:39)
# DLL version V9.60, compiled Jul 15 2026 14:45:49
```

> 程序启动时会自动从 J-Link 驱动导出最新器件列表（执行 `JLinkExe -CommandFile JLinkCommandFile.jlink`），无需手动更新 `JLinkDevicesBuildIn.xml`。
>
> 如果程序启动时导出失败（例如 J-Link 未安装或不在 PATH 中），程序仍会使用已有的 `JLinkDevicesBuildIn.xml` 文件。

---

## 使用方法

### 1. 启动程序

```bash
python main_window.py
```

### 2. GUI 操作步骤

| 步骤 | 操作 |
|------|------|
| **① 选择器件** | 点击 **Selete Device**，在列表中找到你的 MCU 型号，点击选中后按 OK |
| **② 配置接口** | 接口一般选 **SWD**；速率根据 J-Link 型号选择（V9 可选 4000–8000 kHz） |
| **③ 复位（可选）** | 勾选 **Reset target** 在连接时复位目标 MCU |
| **④ 扫描串口** | 点击 **Scan**，在下拉列表中选择虚拟串口对中的**第一个**（如 `/dev/tnt0`、`/dev/ttyS222` 或 `/tmp/ttyV0`） |
| **⑤ 设置波特率** | 选择与目标 RTT 匹配的波特率（常用 **115200**） |
| **⑥ 启动桥接** | 点击 **Start** 开始转换 |

### 3. 连接串口终端

打开串口终端工具，连接虚拟串口对中的**另一个**设备：

**Linux：**

```bash
# 方式一：minicom
minicom -D /dev/tnt1 -b 115200

# 方式二：screen（退出按 Ctrl+A 然后 K）
screen /dev/tnt1 115200

# 方式三：VOFA+ 等图形工具
# 使用 tty0tty 时端口列表会自动出现 /dev/tnt1
# 使用 socat 时在端口栏手动输入 /tmp/ttyV1
```

**Windows：**
打开 Putty 或 SSCOM，选择虚拟串口对中的另一个（如 COM5），波特率设为与 RTT2UART 一致。

---

## 接入方式说明

程序支持三种 J-Link 连接方式：

| 方式 | 说明 |
|------|------|
| **USB** | 通过 USB 直连 J-Link（最常用）。可勾选 Serial No 并填入序列号以指定特定 J-Link |
| **TCP/IP** | 通过网络连接远程 J-Link 服务器 |
| **Existing Session** | 复用已有的 J-Link 调试会话。勾选 Auto reconnect 支持断线自动重连 |

---

## 常见问题

### 找不到目标器件

程序启动时**会自动**调用 `JLinkExe` 导出 J-Link 驱动支持的全部器件列表。如果你在器件选择列表中找不到目标芯片：

**方法一：手动更新器件列表（推荐）**

```bash
cd RTT2UART
JLinkExe -CommandFile JLinkCommandFile.jlink
```

执行后会更新 `JLinkDevicesBuildIn.xml`，重启程序即可看到最新器件列表。

**方法二：检查 J-Link 驱动版本**

J-Link 驱动版本过旧可能不支持新型号 MCU，升级到最新版：

```bash
# 查看当前版本
JLinkExe -? | head -1
```

访问 [SEGGER 下载页](https://www.segger.com/downloads/jlink/) 获取最新驱动。

### J-Link 库找不到

```bash
export LD_LIBRARY_PATH=/opt/SEGGER/JLink:$LD_LIBRARY_PATH
```

可将此行加入 `~/.bashrc` 使其永久生效：

```bash
echo 'export LD_LIBRARY_PATH=/opt/SEGGER/JLink:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

### Linux 串口权限不足

```bash
sudo usermod -a -G dialout $USER
# 注销后重新登录生效
```

### socat 报端口占用

先杀掉残留的 socat 进程：

```bash
pkill socat
```

### tty0tty 模块加载失败

重新编译并加载：

```bash
cd /tmp/tty0tty/module
make clean && make
sudo cp tty0tty.ko /lib/modules/$(uname -r)/kernel/drivers/tty/
sudo depmod
sudo modprobe tty0tty
sudo chmod 660 /dev/tnt*
sudo chown root:dialout /dev/tnt*
```

> 内核更新后需要重新编译并安装模块。

---

## 打包为独立程序

```bash
pyinstaller --onefile --name rtt2uart --noconsole -i ./swap_horiz_16px.ico ./main_window.py
```

---

## 开发

### 生成 UI Python 类

```bash
pyside6-uic rtt2uart.ui -o ui_rtt2uart.py
pyside6-uic sel_device.ui -o ui_sel_device.py
```

### 生成资源文件 Python 类

```bash
pyside6-rcc icons.qrc -o rc_icons.py
```
