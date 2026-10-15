# Cloud & infrastructure projects

[← Back to profile](https://github.com/JoannaKHughes)

Private repositories are listed by name.

|  | Project | Description | Built with |
|---|---|---|---|
| <img src="../assets/icons/mapping-aws.svg" width="40" alt=""> | longreadMapping_AWS (private) | Terraform-deployed EC2 environment for mapping ONT (minimap2) and PacBio (pbmm2) reads on ARM64 or x86_64 | Terraform · AWS EC2 · S3 · IAM · Docker · minimap2 · pbmm2 |
| <img src="../assets/icons/basecall-aws.svg" width="40" alt=""> | longreadBasecalling_AWS (private) | Terraform configuration for a GPU EC2 instance that runs Dorado basecalling on Oxford Nanopore data, producing BAM and FASTQ | Terraform · AWS EC2 (GPU) · S3 · Docker · Dorado |
| <img src="../assets/icons/wgs-s3.svg" width="40" alt=""> | wgs_s3 (private) | S3 buckets for raw and analysis sequencing data: Terraform, lifecycle rules (Deep Archive / Intelligent-Tiering) and sample inventory scripts | Terraform · AWS S3 (lifecycle, Glacier Deep Archive) · Python · boto3 · pandas · openpyxl |
| <img src="../assets/icons/shortread.svg" width="40" alt=""> | batch_nextflow_shortread (private) | Short-read sister pipeline to PACER: bwa mapping and Manta/Delly SV calling on AWS Batch | Nextflow · AWS Batch · Terraform · Docker · bwa · Manta · Delly |
| <img src="../assets/icons/orchestrator.svg" width="40" alt=""> | basecall_orchestrator (private) | Orchestrates GPU Dorado basecalling runs on EC2 | Shell · Terraform · AWS EC2 · CloudWatch · SNS |
| <img src="../assets/icons/mcp.svg" width="40" alt=""> | pipeline_status_mcp (private) | Read-only MCP server that reports PACER job and queue status | Python · MCP SDK · boto3 · asyncio |
