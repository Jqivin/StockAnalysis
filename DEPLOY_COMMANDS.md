# 服务器部署命令手册

## 服务器信息
- **IP**: 60.205.188.111
- **用户**: 请根据实际情况填写（建议使用普通用户而非root）

---

## 方案一：使用自动化脚本（推荐）

### 1. 在本地Windows执行（PowerShell或Git Bash）

```bash
# 压缩项目
cd D:\01_Jqivin\stock
tar -czf stock.tar.gz --exclude='venv' --exclude='logs' --exclude='__pycache__' --exclude='*.pyc' .

# 上传到服务器（替换your_username）
scp stock.tar.gz your_username@60.205.188.111:/tmp/
```

### 2. 登录服务器执行部署

```bash
# 登录服务器
ssh your_username@60.205.188.111

# 创建项目目录
mkdir -p ~/stock
cd ~/stock

# 解压
tar -xzf /tmp/stock.tar.gz
rm /tmp/stock.tar.gz

# 一键部署
bash deploy.sh
```

---

## 方案二：手动部署（详细步骤）

### 步骤1：上传项目

```bash
# 在本地执行
cd D:\01_Jqivin\stock
scp -r . your_username@60.205.188.111:~/stock/
```

### 步骤2：登录服务器

```bash
ssh your_username@60.205.188.111
```

### 步骤3：安装依赖

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git

# CentOS/RHEL
sudo yum install -y python3 python3-pip git
```

### 步骤4：创建虚拟环境

```bash
cd ~/stock
python3 -m venv venv
source venv/bin/activate
```

### 步骤5：安装Python包

```bash
pip install pandas numpy akshare baostock schedule
```

### 步骤6：配置邮箱

```bash
# 编辑配置
nano config/email_config.json
```

填入你的信息：
```json
{
  "smtp_server": "smtp.163.com",
  "smtp_port": 465,
  "sender_email": "18791022456@163.com",
  "sender_password": "你的授权码",
  "receiver_emails": ["jqivin@163.com"]
}
```

### 步骤7：测试

```bash
source venv/bin/activate
python test_email.py
```

### 步骤8：启动

```bash
# 前台运行（测试）
./start_strategy.sh

# 后台运行
nohup ./start_strategy.sh > /dev/null 2>&1 &

# 查看日志
tail -f logs/strategy.log
```

---

## 方案三：使用rsync同步（适合后续更新）

```bash
# 在本地执行
rsync -avz --exclude='venv' --exclude='logs' --exclude='__pycache__' \
  D:\01_Jqivin\stock/ your_username@60.205.188.111:~/stock/
```

---

## 服务器上的一键部署脚本

将以下内容保存为 `~/stock/quick_deploy.sh`：

```bash
#!/bin/bash
set -e

echo "========================================"
echo "快速部署脚本"
echo "========================================"

cd ~/stock

# 1. 安装依赖
echo "安装系统依赖..."
if command -v apt-get &> /dev/null; then
    sudo apt update && sudo apt install -y python3 python3-pip python3-venv git
elif command -v yum &> /dev/null; then
    sudo yum install -y python3 python3-pip git
fi

# 2. 虚拟环境
echo "创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 3. 安装包
echo "安装Python包..."
pip install pandas numpy akshare baostock schedule

# 4. 配置
echo "配置文件..."
mkdir -p logs config
if [ ! -f "config/email_config.json" ]; then
    cp config/email_config.example.json config/email_config.json
    echo "请编辑 config/email_config.json 配置邮箱"
fi

# 5. 权限
chmod +x start_strategy.sh monitor.sh deploy.sh 2>/dev/null || true

echo "========================================"
echo "部署完成！"
echo "========================================"
```

使用：
```bash
chmod +x ~/stock/quick_deploy.sh
~/stock/quick_deploy.sh
```

---

## 检查部署状态

```bash
# 检查进程
ps aux | grep daily.py

# 检查日志
tail -50 ~/stock/logs/strategy.log

# 检查Python环境
source ~/stock/venv/bin/activate
python --version
pip list
```

---

## 常见问题

### SSH连接失败
```bash
# 检查服务器SSH状态
sudo systemctl status sshd

# 启动SSH
sudo systemctl start sshd

# 检查防火墙
sudo firewall-cmd --list-ports
sudo firewall-cmd --add-port=22/tcp --permanent
sudo firewall-cmd --reload
```

### Python安装失败
```bash
# 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pandas
```

### 权限问题
```bash
# 修改所有者
sudo chown -R your_username:your_username ~/stock
```

---

## 快速命令参考

| 操作 | 命令 |
|------|------|
| 上传 | `scp -r stock/ user@60.205.188.111:~/stock/` |
| 登录 | `ssh user@60.205.188.111` |
| 启动 | `cd ~/stock && ./start_strategy.sh` |
| 后台 | `nohup ./start_strategy.sh &` |
| 停止 | `pkill -f daily.py` |
| 日志 | `tail -f ~/stock/logs/strategy.log` |
