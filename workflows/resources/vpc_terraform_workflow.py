from __future__ import annotations

from datetime import timedelta

from temporalio import workflow


@workflow.defn
class VPCWorkflow:
    @workflow.run
    async def run(self, vpc_cidr: str) -> str:
        workflow.logger.info("Starting Terraform init for VPC CIDR %s", vpc_cidr)
        return await workflow.execute_activity(
            "terraform_init_vpc_activity",
            start_to_close_timeout=timedelta(minutes=1),
        )
