# Wallet Watch

公开网站：https://jessie-wallet-watch.proudbuttercup1.chatgpt.site

普通 Python + GitHub Actions 定时触发，无大模型调用。

- 每5分钟计划触发（第2、7、12…分钟），GitHub可能延迟；不是秒级告警服务。
- Python调用网站服务端采集器，Alchemy凭证、数据库和断点均在网站托管环境。
- 使用GitHub OIDC短期身份。网站校验仓库ID、所有者ID、main分支、工作流路径、有效期、受众和签名。其他仓库及PR不能触发采集。不需要把Alchemy Key或长期调度密钥放入仓库。
- 按最终确认区块增量采集，重叠128块补漏；稳定转移ID防重复；采集/聚合游标支持重跑。
- 发布完整批次后从公开接口读回验证；失败Actions显示红色，网站保留旧批次并显示错误/延迟。
- 初始仅Ethereum候选钱包，ETH/USDT/USDC。名单用途未确认，来源索引完整性未独立证明。
- 固定阈值异常仅供人工核查；30天基线不足时明确标注。
- 请求统计不等同于计费CU，以Alchemy账单为准。默认每天最多5000 RPC尝试。
- GitHub公开仓库长期无活动可能停用定时工作流；需要定期检查Actions与网页的最后更新时间。

## 手动运行
仓库Actions → Wallet collection → Run workflow。

## 文件
`collect.py`：有限时长的一轮同步与验收；`.github/workflows/collect.yml`：云调度。
