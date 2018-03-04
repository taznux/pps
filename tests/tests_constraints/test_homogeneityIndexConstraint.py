from core.types import PriorityType, ResultType
from tests.conftest import planning_item


def test_constrain(converter):
    structure_name = 'PTV70-BR.PLX 4MM'
    constrain = 'HI70Gy[] <= 0.08'
    max_dc = converter.convert_to_dvh_constraint(structure_name, PriorityType.IDEAL, constrain)
    constrain_result = max_dc.constrain(planning_item)
    assert not constrain_result.is_success
    assert constrain_result.result_type == ResultType.ACTION_LEVEL_1