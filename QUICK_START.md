# 快速部署指南

## 最简部署（3步完成）

### 1. 上传项目到服务器

```bash
# 压缩项目（本地）
tar -czf stock.tar.gz stock/

# 上传到服务器
scp stock.tar.gz user@your-server:/home/user/

# 解压（服务器）
cd /home/user
tar -xzf stock.tar.gz
cd stock
```

### 2. 运行一键部署

```bash
chmod +x deploy.sh
./deploy.sh
```

### 3. 配置邮箱并启动

```bash
# 编辑邮箱配置
nano config/email_config.json

# 测试邮件
source venv/bin/activate
python test_email.py

# 启动策略
./start_strategy.sh
```

---

## 后台运行

### 方式1：nohup（最简单）

```bash
nohup ./start_strategy.sh > /dev/null 2>&1 &

# 查看进程
ps aux | grep daily.py

# 停止
pkill -f daily.py
```

### 方式2：screen（推荐）

```bash
# 安装screen
sudo apt install -y screen

# 创建会话
screen -S stock

# 运行策略
./start_strategy.sh

# 分离会话：Ctrl+A, D
# 重新连接：screen -r stock
```

### 方式3：systemd（生产环境）

```bash
# 1. 修改服务文件中的用户名
sed -i 's/YOUR_USERNAME/your_username/g' stock-strategy.service

# 2. 复制到systemd目录
sudo cp stock-strategy.service /etc/systemd/system/

# 3. 重载并启动
sudo systemctl daemon-reload
sudo systemctl start stock-strategy
sudo systemctl enable stock-strategy

# 4. 查看状态
sudo systemctl status stock-strategy

# 5. 查看日志
sudo journalctl -u stock-strategy -f
```

---

## 监控与维护

### 添加自动监控（每5分钟检查）

```bash
chmod +x monitor.sh
crontab -e

# 添加这一行
*/5 * * * * cd /home/user/stock && ./monitor.sh >> logs/monitor.log 2>&1
```

### 查看日志

```bash
# 实时日志
tail -f logs/strategy.log

# 最近100行
tail -n 100 logs/strategy.log

# 错误日志
tail -f logs/error.log

# 监控日志
tail -f logs/monitor.log
```

### 清理旧日志

```bash
# 删除30天前的日志
find logs/ -name "*.log" -mtime +30 -delete
```

---

## 更新代码

```bash
cd /home/user/stock
git pull origin main

# 重启
sudo systemctl restart stock-strategy
# 或
pkill -f daily.py && nohup ./start_strategy.sh > /dev/null 2>&1 &
```

---

## 常用命令

| 操作 | 命令 |
|------|------|
| 启动策略 | `./start_strategy.sh` |
| 后台启动 | `nohup ./start_strategy.sh > /dev/null 2>&1 &` |
| 停止策略 | `pkill -f daily.py` |
| 查看进程 | `ps aux \| grep daily.py` |
| 查看日志 | `tail -f logs/strategy.log` |
| 测试邮件 | `python test_email.py` |
| 运行回测 | `python backtest_full_flow.py` |

---

## 端口与防火墙

默认不需要开放端口（策略使用对外数据源，不提供服务）

如需远程访问服务器：
```bash
# 开放SSH
sudo ufw allow 22/tcp
sudo ufw enable
```

---

## 时区设置

```bash
# 设置为上海时间
sudo timedatectl set-timezone Asia/Shanghai

# 查看时区
timedatectl
```

---

## 故障排查

### 1. 策略不运行

```bash
# 检查进程
ps aux | grep daily.py

# 检查日志
tail -50 logs/error.log

# 手动运行看错误
./start_strategy.sh
```

### 2. 邮件发送失败

```bash
# 测试邮件
python test_email.py

# 检查配置
cat config/email_config.json
```

### 3. 网络问题

```bash
# 测试网络连接
ping -c 4 www.baidu.com

# 测试数据源连接
python -c "import akshare; print('AkShare OK')"
```

---

## 目录结构

```
stock/
├── daily.py                  # 主程序
├── deploy.sh                 # 一键部署脚本
├── start_strategy.sh         # 启动脚本
├── monitor.sh                # 监控脚本
├── DEPLOYMENT.md             # 详细部署文档
├── config/
│   ├── email_config.json     # 邮件配置
│   ├── email_config.example.json
│   └── rules.json            # 交易规则
├── logs/                     # 日志目录
│   ├── strategy.log
│   ├── error.log
│   └── monitor.log
├── data/                     # 数据模块
├── strategy/                 # 策略模块
├── realtime/                 # 实时监控
├── signals/                  # 信号推送
├── scheduler.py              # 定时调度
└── venv/                     # Python虚拟环境
```

---

## 技术支持

- 详细文档: `DEPLOYMENT.md`
- 日志文件: `logs/`
- 配置文件: `config/`
