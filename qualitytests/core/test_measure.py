import uuid

import pytest
import asyncio
from pytest_mock import MockerFixture
pytest_plugins = ('pytest_asyncio',)

import qualitytests_utils

from core import measure
from core.exceptions import PatternDoesNotExists

@pytest.mark.asyncio
class TestMeasure:


    async def test_raise_pattern_not_found_measure_pattern_by_pattern_id(self, tmp_path, capsys, mocker):
        init = {}
        qualitytests_utils.init_measure_test(init, mocker)
        assert init["patterns"] == [1,2,3]
        pattern_id: int = 2
        mocker.patch("core.pattern_operations.start_add_measurement_for_pattern",
                     side_effect=PatternDoesNotExists(pattern_id))
        await measure.measure_list_patterns([pattern_id], init["language"], init["tools"], init["tp_lib_path"], 3)
        captured = capsys.readouterr()
        assert f"Pattern id {pattern_id} is not found" in captured.out


    async def test_measure_list_patterns(self, mocker: MockerFixture):
        init = {}
        qualitytests_utils.init_measure_test(init, mocker)
        assert init["patterns"] == [1, 2, 3]
        task_mock = mocker.patch("core.pattern_operations.start_add_measurement_for_pattern",
                                 return_value=[uuid.uuid4() for _ in range(10)])
        mocker.patch("core.pattern_operations.save_measurement_for_pattern")
        d_res = await measure.measure_list_patterns([1, 2], init["language"], init["tools"], init["tp_lib_path"], 3)
        assert d_res['measured_patterns_ids'] == [1, 2]
        assert task_mock.call_count == 2