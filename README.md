# Hyperliquid 聪明钱监控机器人

监控指定 Hyperliquid 地址的永续合约交易，并通过飞书 Webhook 发送实时通知。

## 功能

- **实时监控**: 监听开仓、平仓、加仓、减仓、反手信号。
- **飞书推送**: 发送详细的富文本卡片消息。
- **Docker部署**: 一键启动，长期运行。

## 快速开始

### 1. 配置

修改 `config.yaml` 文件：

```yaml
monitor:
  addresses:
    - "0x9c2a2a966ed8e47f0c8b7e2ec2b91424f229f6a8" # 监控地址

feishu:
  webhook_url: "https://open.larksuite.com/..." # 你的飞书 Webhook URL
```

### 2. 使用 Docker 运行 (推荐)

```bash
docker-compose up -d --build
```

查看日志：
```bash
docker-compose logs -f
```

### 3. 本地运行

安装依赖：
```bash
pip install -r requirements.txt
```

运行：
```bash
python src/main.py
```

## 信号说明

- **OPEN**: 新建仓位
- **CLOSE**: 完全平仓
- **INCREASE**: 同向加仓
- **DECREASE**: 同向减仓
- **REVERSE**: 反向开仓（反手）
