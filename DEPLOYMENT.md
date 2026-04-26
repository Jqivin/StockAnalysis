# A股短线交易系统 - 部署指南

## 一、服务器要求

### 最低配置
- **操作系统**: Linux (Ubuntu 20.04+ / CentOS 7+ / Debian 10+)
- **CPU**: 2核
- **内存**: 2GB
- **硬盘**: 10GB
- **网络**: 稳定的互联网连接

### 推荐配置
- **操作系统**: Ubuntu 22.04 LTS
- **CPU**: 4核
- **内存**: 4GB
- **硬盘**: 20GB SSD
- **网络**: 100Mbps+

---

## 二、部署步骤

### 1. 上传项目到服务器

```bash
# 方法1: 使用 scp
scp -r /本地路径/stock user@服务器IP:/home/user/

# 方法2: 使用 Git (如果项目在GitHub)
git clone https://github.com/your-repo/stock.git
cd stock

# 方法3: 先压缩再上传
tar -czf stock.tar.gz stock/
scp stock.tar.gz user@服务器IP:/home/user/
# 在服务器上解压
tar -xzf stock.tar.gz
```

### 2. 安装Python环境

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git

# CentOS/RHEL
sudo yum install -y python3 python3-pip git
```

### 3. 创建虚拟环境

```bash
cd /home/user/stock
python3 -m venv venv
source venv/bin/activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt

# 如果 requirements.txt 不存在，手动安装
pip install pandas numpy akshare baostock schedule matplotlib plotly
```

### 5. 配置文件

```bash
# 复制配置模板
cp config/email_config.example.json config/email_config.json

# 编辑配置
nano config/email_config.json
```

填入你的邮箱信息：
```json
{
  "smtp_server": "smtp.163.com",
  "smtp_port": 465,
  "sender_email": "your_email@163.com",
  "sender_password": "your_authorization_code",
  "receiver_emails": ["receiver@example.com"]
}
```

### 6. 测试运行

```bash
# 激活虚拟环境
source venv/bin/activate

# 测试邮件发送
python test_email.py

# 测试定时调度
python test_scheduler.py

# 运行完整回测
python backtest_full_flow.py
```

---

## 三、后台运行方案

### 方案1: 使用 nohup (简单)

```bash
# 创建启动脚本
cat > start_strategy.sh << 'EOF'
#!/bin/bash
cd /home/user/stock
source venv/bin/activate

# 记录启动时间
echo "策略启动: $(date)" >> logs/strategy.log

# 启动主程序
python -u daily.py >> logs/strategy.log 2>&1
EOF

chmod +x start_strategy.sh

# 后台运行
nohup ./start_strategy.sh > /dev/null 2>&1 &

# 查看进程
ps aux | grep daily.py

# 查看日志
tail -f logs/strategy.log
```

### 方案2: 使用 screen (推荐)

```bash
# 安装 screen
sudo apt install -y screen  # Ubuntu/Debian
# sudo yum install -y screen  # CentOS/RHEL

# 创建会话
screen -S stock_strategy

# 在会话中运行
cd /home/user/stock
source venv/bin/activate
python daily.py

# 分离会话: Ctrl+A, D

# 重新连接
screen -r stock_strategy

# 查看所有会话
screen -ls
```

### 方案3: 使用 systemd (生产环境推荐)

```bash
# 创建服务文件
sudo nano /etc/systemd/system/stock-strategy.service
```

写入以下内容：
```ini
[Unit]
Description=A股短线交易策略
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/user/stock
Environment="PATH=/home/user/stock/venv/bin"
ExecStart=/home/user/stock/venv/bin/python daily.py
Restart=always
RestartSec=10
StandardOutput=append:/home/user/stock/logs/strategy.log
StandardError=append:/home/user/stock/logs/error.log

[Install]
WantedBy=multi-user.target
```

```bash
# 重载systemd配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start stock-strategy

# 设置开机自启
sudo systemctl enable stock-strategy

# 查看状态
sudo systemctl status stock-strategy

# 查看日志
sudo journalctl -u stock-strategy -f

# 停止服务
sudo systemctl stop stock-strategy

# 重启服务
sudo systemctl restart stock-strategy
```

### 方案4: 使用 cron (定时任务)

```bash
# 编辑crontab
crontab -e

# 添加定时任务
# 每天8:25启动策略
25 8 * * * cd /home/user/stock && /home/user/stock/venv/bin/python daily.py >> logs/cron.log 2>&1

# 查看定时任务
crontab -l
```

---

## 四、创建启动脚本

```bash
# 创建启动脚本
cat > run_strategy.sh << 'EOF'
#!/bin/bash

# 设置工作目录
cd /home/user/stock

# 激活虚拟环境
source venv/bin/activate

# 创建日志目录
mkdir -p logs

# 记录启动信息
echo "========================================" >> logs/strategy.log
echo "策略启动时间: $(date '+%Y-%m-%d %H:%M:%S')" >> logs/strategy.log
echo "========================================" >> logs/strategy.log

# 运行策略
python daily.py 2>&1 | tee -a logs/strategy.log
EOF

chmod +x run_strategy.sh

# 运行
./run_strategy.sh
```

---

## 五、日志管理

### 日志轮转配置

```bash
# 安装 logrotate
sudo apt install -y logrotate

# 创建配置文件
sudo nano /etc/logrotate.d/stock-strategy
```

写入以下内容：
```
/home/user/stock/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 your_username your_username
}
```

### 查看日志

```bash
# 实时查看
tail -f logs/strategy.log

# 查看最近100行
tail -n 100 logs/strategy.log

# 搜索错误
grep -i "error" logs/strategy.log

# 查看今天的日志
grep "$(date +%Y-%m-%d)" logs/strategy.log
```

---

## 六、监控与告警

### 监控脚本

```bash
cat > monitor.sh << 'EOF'
#!/bin/bash

# 检查进程是否运行
if ! pgrep -f "daily.py" > /dev/null; then
    echo "策略进程未运行，正在重启..."
    cd /home/user/stock
    source venv/bin/activate
    nohup python daily.py >> logs/strategy.log 2>&1 &
    echo "策略已重启: $(date)" >> logs/restart.log
else
    echo "策略运行正常: $(date)"
fi
EOF

chmod +x monitor.sh

# 添加到crontab，每5分钟检查一次
# */5 * * * * /home/user/stock/monitor.sh >> logs/monitor.log 2>&1
```

---

## 七、防火墙配置

```bash
# 如果需要远程访问（可选）
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP（如果需要Web界面）
sudo ufw enable
```

---

## 八、更新与维护

### 更新代码

```bash
# 如果使用Git
cd /home/user/stock
git pull origin main

# 重启服务
sudo systemctl restart stock-strategy
# 或者
pkill -f daily.py
nohup ./run_strategy.sh &
```

### 清理旧日志

```bash
# 删除30天前的日志
find logs/ -name "*.log" -mtime +30 -delete

# 清理压缩的旧日志
find logs/ -name "*.gz" -mtime +60 -delete
```

---

## 九、快速部署一键脚本

```bash
cat > deploy.sh << 'EOF'
#!/bin/bash

set -e

echo "开始部署A股短线交易系统..."

# 1. 安装依赖
echo "安装Python依赖..."
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git

# 2. 创建虚拟环境
echo "创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 3. 安装Python包
echo "安装Python包..."
pip install pandas numpy akshare baostock schedule

# 4. 创建日志目录
mkdir -p logs

# 5. 提示配置
echo "========================================"
echo "部署完成！"
echo "========================================"
echo ""
echo "下一步："
echo "1. 编辑 config/email_config.json 配置邮箱"
echo "2. 运行测试: python test_email.py"
echo "3. 启动策略: ./run_strategy.sh"
echo ""
EOF

chmod +x deploy.sh
./deploy.sh
```

---

## 十、常见问题

### Q1: 依赖安装失败
```bash
# 使用国内镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pandas
```

### Q2: 网络连接问题
```bash
# 配置代理（如果需要）
export http_proxy=http://proxy:port
export https_proxy=http://proxy:port
```

### Q3: 时区问题
```bash
# 设置时区为上海时间
sudo timedatectl set-timezone Asia/Shanghai
```

### Q4: 权限问题
```bash
# 确保脚本有执行权限
chmod +x *.sh
```

---

## 十一、安全建议

1. **修改默认端口**: 修改SSH默认端口22
2. **使用密钥登录**: 禁用密码登录，使用SSH密钥
3. **防火墙**: 只开放必要端口
4. **定期更新**: `sudo apt update && sudo apt upgrade`
5. **备份数据**: 定期备份配置文件和日志
6. **限制访问**: 使用iptables限制IP访问

---

## 十二、联系方式

如有问题，请查看：
- 日志文件: `logs/strategy.log`
- 错误日志: `logs/error.log`
- 重启日志: `logs/restart.log`
