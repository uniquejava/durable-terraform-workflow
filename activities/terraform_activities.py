from temporalio import activity

import json
import re
from pathlib import Path
from typing import Optional, Union


from utils.cmds import (
    run_tf_init_command,
    run_tf_plan_with_tfvars,
    run_tf_apply_with_tfvars,
)

TERRAFORM_EC2_DIR = Path(__file__).parent.parent / "terraform" / "compute"
TFVARS_PATH = TERRAFORM_EC2_DIR / "infra.auto.tfvars"
INIT_SUCCESS_TOKEN = "Terraform has been successfully initialized"
PLAN_SUMMARY_PATTERN = re.compile(
    r"Plan:\s+(\d+)\s+to add,\s+(\d+)\s+to change,\s+(\d+)\s+to destroy",
    re.IGNORECASE,
)
APPLY_SUMMARY_PATTERN = re.compile(
    r"Apply complete!\s+Resources:\s+(\d+)\s+added,\s+(\d+)\s+changed,\s+(\d+)\s+destroyed\.",
    re.IGNORECASE,
)
RESOURCE_ID_PATTERN = re.compile(
    r"^(?P<resource>[A-Za-z0-9_.-]+):\s+Creation complete.*\[id=(?P<id>[^\]]+)\]",
    re.MULTILINE,
)

ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_PATTERN.sub("", text)


@activity.defn(name="terraform_init_activity")
async def terraform_init_activity(directory: Union[str, Path]) -> dict:
    activity.logger.info("Initializing the Terraform init activity")
    raw_output = await run_tf_init_command(directory)
    cleaned = _strip_ansi(raw_output)
    success = INIT_SUCCESS_TOKEN in cleaned
    return {
        "stage": "init",
        "success": success,
        "summary": (
            "Terraform initialization completed successfully"
            if success
            else "Terraform initialization did not complete successfully"
        ),
    }


@activity.defn(name="terraform_plan_activity")
async def terraform_plan_activity(
    directory: Union[str, Path],
    tfvars_path: Union[str, Path] = TFVARS_PATH,
    overrides: Optional[dict] = None,
) -> dict:
    activity.logger.info("在目录 %s 运行 terraform plan", directory)
    if overrides:
        activity.logger.info("使用工作流传入的变量覆盖值执行 plan，忽略 tfvars 文件")
        raw_output = await run_tf_plan_with_tfvars(
            directory,
            vars_mapping=overrides,
        )
    else:
        activity.logger.info("未提供覆盖值，使用 tfvars 文件 %s 执行 plan", tfvars_path)
        raw_output = await run_tf_plan_with_tfvars(
            directory,
            tfvars_path=tfvars_path or TFVARS_PATH,
        )
    cleaned = _strip_ansi(raw_output)
    match = PLAN_SUMMARY_PATTERN.search(cleaned)
    summary = None
    if match:
        summary = {
            "add": int(match.group(1)),
            "change": int(match.group(2)),
            "destroy": int(match.group(3)),
        }
    return {
        "stage": "plan",
        "success": summary is not None,
        "summary": summary,
    }

@activity.defn(name="terraform_apply_activity")
async def terraform_apply_activity(
    overrides: Optional[dict] = None,
    directory: Union[str, Path] = TERRAFORM_EC2_DIR,
    tfvars_path: Union[str, Path] = TFVARS_PATH,
) -> dict:
    if overrides:
        activity.logger.info("使用工作流传入的变量覆盖值执行 apply，忽略 tfvars 文件")
        raw_output = await run_tf_apply_with_tfvars(
            directory,
            vars_mapping=overrides,
        )
    else:
        activity.logger.info("未提供覆盖值，使用 tfvars 文件 %s 执行 apply", tfvars_path)
        raw_output = await run_tf_apply_with_tfvars(
            directory,
            tfvars_path=tfvars_path,
        )
    cleaned = _strip_ansi(raw_output)
    match = APPLY_SUMMARY_PATTERN.search(cleaned)
    summary = None
    if match:
        summary = {
            "add": int(match.group(1)),
            "change": int(match.group(2)),
            "destroy": int(match.group(3)),
        }
    resources = [
        {"resource": m.group("resource"), "id": m.group("id")}
        for m in RESOURCE_ID_PATTERN.finditer(cleaned)
    ]
    completion_line = match.group(0) if match else "Apply summary unavailable"
    return {
        "stage": "apply",
        "success": summary is not None,
        "summary": summary,
        "completion": completion_line,
        "resources": resources,
    }
