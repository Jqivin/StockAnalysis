# Screen 使用指南

## 📋 文件说明

| 文件 | 功能 |
|------|------|
| `run_with_screen.sh` | 启动策略程序（使用screen） |
| `stop_with_screen.sh` | 停止策略程序 |
| `view_logs.sh` | 查看日志 |
| `check_status.sh` | 检查运行状态 |

---

## 🚀 快速开始

### 1. 上传脚本到服务器

```bash
# 在本地执行
scp run_with_screen.sh stop_with_screen.sh view_logs.sh check_status.sh root@60.205.188.111:/root/stock/
```

### 2. 设置执行权限

```bash
# 在服务器上执行
cd /root/stock
chmod +x run_with_screen.sh stop_with_screen.sh view_logs.sh check_status.sh
```

---

## 📖 使用说明

### 启动程序

```bash
cd /root/stock
./run_with_screen.sh
```

脚本会：
1. 检查screen是否安装
2. 检查是否有已存在的会话
3. 在screen中启动程序
4. 询问是否立即连接查看输出

### 停止程序

```bash
cd /root/stock
./stop_with_screen.sh
```

### 查看日志

```bash
cd /root/stock
./view_logs.sh
```

提供多种查看方式：
- 实时查看（类似tail -f）
- 查看最近N行
- 查看错误日志
- 搜索内容
- 查看今天的日志

### 检查状态

```bash
cd /root/stock
./check_status.sh
```

显示：
- 进程运行状态
- Screen会话状态
- 日志文件信息
- Python环境
- 配置文件状态

---

## ⌨️ Screen 常用命令

### 基本操作

| 命令 | 说明 |
|------|------|
| `screen -S stock` | 创建名为stock的会话 |
| `screen -r stock` | 重新连接到名为stock的会话 |
| `screen -x stock` | 强制连接到会话（如果被占用） |
| `screen -ls` | 列出所有会话 |
| `screen -S stock -X quit` | 终止名为stock的会话 |

### 在Screen中

| 快捷键 | 说明 |
|--------|------|
| `Ctrl+A, D` | 分离会话（程序继续运行） |
| `Ctrl+A, C` | 创建新窗口 |
| `Ctrl+A, N` | 切换到下一个窗口 |
| `Ctrl+A, P` | 切换到上一个窗口 |
| `Ctrl+A, K` | 杀死当前窗口 |
| `Ctrl+A, \` | 切换到上一个会话 |
| `Ctrl+A, A` | 命名当前窗口 |

---

## 🔄 完整工作流程

### 首次运行

```bash
# 1. 上传脚本
scp *.sh root@60.205.188.111:/root/stock/

# 2. 登录服务器
ssh root@60.205.188.111

# 3. 进入目录
cd /root/stock

# 4. 设置权限
chmod +x *.sh

# 5. 启动程序
./run_with_screen.sh
```

### 日常使用

```bash
# 登录服务器
ssh root@60.205.188.111

# 检查状态
cd /root/stock
./check_status.sh

# 如果需要查看实时输出
screen -r stock_strategy

# 分离会话（在screen中按 Ctrl+A, D）

# 查看日志
./view_logs.sh

# 如果需要停止
./stop_with_screen.sh
```

### 重新启动

```bash
# 先停止
./stop_with_screen.sh

# 再启动
./run_with_screen.sh
```

---

## 📊 状态说明

### check_status.sh 输出解读

**【1】进程状态**
- ✓ 绿色 = 程序正在运行
- ✗ 红色 = 程序未运行

**【2】Screen会话**
- ✓ 绿色 = Screen会话存在
- ○ 黄色 = Screen会话不存在

**【3】日志文件**
- ✓ 绿色 = 日志文件存在
- ○ 黄色 = 日志文件不存在

**【4】Python环境**
- ✓ 绿色 = 虚拟环境存在
- ✗ 红色 = 虚拟环境不存在

**【5】配置文件**
- ✓ 绿色 = 配置存在
- ○ 黄色 = 配置不存在
- ⚠ 黄色 = 需要配置邮箱

---

## ❓ 常见问题

### Q1: Screen会话已存在怎么办？

脚本会提示你选择：
1. 重新连接到现有会话
2. 终止现有会话并创建新会话
3. 取消操作

### Q2: 程序崩溃了怎么重启？

```bash
# 方法1：使用脚本
./stop_with_screen.sh
./run_with_screen.sh

# 方法2：手动操作
screen -S stock_strategy -X quit
pkill -f daily.py
cd /root/stock
./run_with_screen.sh
```

### Q3: 如何查看程序实时输出？

```bash
# 方法1：连接到screen
screen -r stock_strategy

# 方法2：查看日志
tail -f /root/stock/logs/strategy.log
```

### Q4: 关闭XShell后程序会停止吗？

**不会！** 使用screen后：
- 关闭XShell → 程序继续运行
- 重新SSH登录 → 用 `screen -r stock_strategy` 重新连接

### Q5: 如何知道程序是否在运行？

```bash
# 方法1：使用状态脚本
./check_status.sh

# 方法2：检查进程
ps aux | grep daily.py | grep -v grep

# 方法3：检查screen
screen -ls | grep stock_strategy
```

---

## 💡 提示

1. **首次使用**：运行 `./run_with_screen.sh` 后，建议立即连接到screen查看是否有错误
2. **分离会话**：确认程序正常运行后，按 `Ctrl+A, D` 分离
3. **定期检查**：每天运行 `./check_status.sh` 检查程序状态
4. **查看日志**：使用 `./view_logs.sh` 快速查看日志
5. **安全退出**：关闭XShell前确认已分离screen会话

---

## 📞 遇到问题？

1. 查看日志：`./view_logs.sh`
2. 检查状态：`./check_status.sh`
3. 重启程序：`./stop_with_screen.sh && ./run_with_screen.sh`
