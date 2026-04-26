# A股量化分析工具

一个功能全面的Python量化分析工具，支持A股市场的实时行情获取、技术分析、基本面分析和策略回测。

## 功能特性

- **实时行情**: 获取股票实时价格、K线数据
- **技术分析**: MA、MACD、RSI、KDJ、布林带等技术指标
- **基本面分析**: PE、PB、ROE等财务指标
- **回测系统**: 策略回测和性能评估

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

### 获取股票行情

```bash
python main.py --code 000001 --days 30
```

### 运行回测

```bash
python main.py --backtest --strategy ma_cross --code 000001
```

## 项目结构

```
stock/
├── data/           # 数据获取模块
├── analysis/       # 分析模块
├── backtest/       # 回测模块
├── utils/          # 工具模块
├── config/         # 配置模块
└── main.py         # 主入口
```

## 数据源

使用AkShare作为主要数据源，完全免费，无需注册。
