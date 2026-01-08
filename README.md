# Durable Terraform Workflow
使用 Temporal 运行 Terraform init/plan/apply 的演示，包含 VPC 与 Compute（S3 bucket）两个模块，以及定时漂移检测。

YT视频: https://www.youtube.com/watch?v=L8crQ_Elyh0

## 目录与组件
- `workflows/`：父子工作流、漂移检测、worker 与启动脚本。
- `activities/terraform_activities.py`：调用 Terraform CLI 并解析 plan/apply 结果。
- `utils/cmds.py`：封装 Terraform init/plan/apply 调用。
- `terraform/vpc`、`terraform/compute`：示例模块与本地 state/lock（仅演示）。

## 前置
- Python 3.9+，已安装 uv。
- Terraform CLI 在 PATH。
- Temporal 可达（默认 `localhost:7233`，namespace `default`）。
- 已配置 AWS 凭证与 region（环境变量或 AWS 配置文件）。

## 快速开始（uv）
```bash
cd durable-terraform-workflow
uv sync
# 如未运行 Temporal 开发服，可先启动：temporal server start-dev --ui-port 8088

uv run -m workflows.worker                 # 启动 worker，监听队列 MY_TASK_QUEUE
uv run -m workflows.start_workflow         # 触发父工作流，依次执行 VPC 与 Compute
uv run -m workflows.start_drift_workflow   # 启动漂移检测循环（对 VPC 周期性 plan）
```

## 配置与输入
- 工作流入参为 Python dict：
  - VPC：`{"vpc_cidr": "10.0.0.0/16"}`；模块默认 `10.1.0.0/16`，环境名 `temporal-dev`，AZ `["ap-northeast-1a","ap-northeast-1c"]`。
  - Compute：`{"tags": {"Name": "dev-instance"}}`，用于 S3 bucket 标签。
- 优先级：传入的 overrides 最优先；若不传可用 tfvars：
  - `terraform/vpc/infra.auto.tfvars` 示例：
    ```hcl
    vpc_cidr   = "10.0.0.0/16"
    environment = "temporal-dev"
    azs         = ["ap-northeast-1a", "ap-northeast-1c"]
    ```
  - `terraform/compute/infra.auto.tfvars` 示例：
    ```hcl
    tags = { Name = "dev-instance" }
    ```

## Terraform 说明
- VPC 模块：VPC、公网子网、IGW、路由表。
- Compute 模块：示例 S3 bucket。
- 仓库中的本地 state/lock 仅为演示，真实环境建议改为远程状态。

## 常见问题
- Terraform 找不到：确认 CLI 在 PATH。
- Temporal 连接失败：检查地址与 namespace 配置。
- AWS 认证或 region 报错：设置 `AWS_ACCESS_KEY_ID`、`AWS_SECRET_ACCESS_KEY`、`AWS_REGION` 或使用已配置的 profile。
- 计划/应用解析异常：查看 worker 日志，Terraform 文本格式变化时更新 `activities/terraform_activities.py` 中的正则。
