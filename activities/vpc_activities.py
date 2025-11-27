from __future__ import annotations

from pathlib import Path

from temporalio import activity

from utils.cmds import run_tf_init_command

TERRAFORM_VPC_DIR = Path(__file__).parent.parent / "terraform"


@activity.defn(name="terraform_init_vpc_activity")
async def terraform_init_vpc_activity() -> str:
    activity.logger.info("Initiating the Terraform VPC init activity")
    return await run_tf_init_command(TERRAFORM_VPC_DIR)
