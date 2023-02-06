import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict

import logging
from core import loggermgr
logger = logging.getLogger(loggermgr.logger_name(__name__))

import core.utils
from core import utils
from core.instance import Instance
from core.measurement import Measurement
from core.sast import SAST
from core.sast_job_runner import InQueue, OutQueue


async def analyze_pattern_instance(instance: Instance, instance_dir: Path,
                                   tools: list[Dict], language: str,
                                   date: datetime, output_dir: Path) -> list[uuid.UUID]:
    logger.info(f"SAST measurements (async) for pattern instance {instance.instance_id} with {len(tools)} tools: in preparation...")
    job_ids: list[uuid.UUID] = []

    # pattern instance dependencies (if any)
    if instance.compile_dependencies:
        lib_dir: Path = instance.compile_dependencies
        logger.debug(f"Dependencies will be considered {lib_dir}")
    else:
        lib_dir = None
        logger.debug(f"No dependencies will be considered")

    for tool in tools:
        try:
            tool_name: str = tool["name"]
            tool_version: str = tool["version"]

            sast_config: Dict = core.utils.load_sast_specific_config(tool_name, tool_version)
            sast_interface_class: str = sast_config["tool_interface"]
            sast_class = utils.get_class_from_str(sast_interface_class)

            # noinspection PyCallingNonCallable
            sast: SAST = sast_class()
            job_id = uuid.uuid4()
            job_ids.append(job_id)
            InQueue().put_nowait((job_id, tool_name, tool_version, instance, date,
                                  sast.launcher(instance_dir, language, output_dir, lib_dir=lib_dir, measurement=True)))
        except Exception as e:
            logger.warning(f"Failed in SAST measurement of pattern instance {instance.instance_id} with tool {tool}. Instance will be ignored. Exception raised: {utils.get_exception_message(e)}")
            continue
    logger.info(f"SAST measurements (async) for pattern instance {instance.instance_id}: prepared")
    return job_ids


async def inspect_analysis_results(job_ids: list[uuid.UUID], language):
    measurements = []
    while True:
        while True:
            job_id_res, tool_name, tool_version, instance, date, csv_res = await OutQueue().get()
            if job_id_res in job_ids:
                job_ids.remove(job_id_res)
                OutQueue().task_done()
                break
            else:
                OutQueue().task_done()
                OutQueue().put_nowait((job_id_res, tool_name, tool_version, instance, date, csv_res))

        sast_config: Dict = core.utils.load_sast_specific_config(tool_name, tool_version)
        sast_interface_class: str = sast_config["tool_interface"]
        sast_class = utils.get_class_from_str(sast_interface_class)

        # noinspection PyCallingNonCallable
        sast: SAST = sast_class()

        findings: list[Dict] = sast.inspector(csv_res, language)

        if tool_version == "saas":
            tool_version = await sast.get_tool_version()

        finding = findings[0] if findings else None
        measurement: Measurement = Measurement().define_verdict(date, instance, finding, tool_name, tool_version)

        measurements.append(measurement)

        if len(job_ids) == 0:
            break

    return measurements
